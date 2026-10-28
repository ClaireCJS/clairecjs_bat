// Discord Social SDK bridge for PAFPlayer. The licensed SDK is supplied by the
// application's owner; no SDK binary or OAuth credential is stored in source.
#define DISCORDPP_IMPLEMENTATION
#include "discordpp.h"
#include <windows.h>
#include <wincred.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <iostream>
#include <memory>
#include <mutex>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {
std::mutex output_mutex;
void status(const std::string& value) {
    std::lock_guard<std::mutex> guard(output_mutex);
    std::cout << "STATUS\t" << value << std::endl;
}
void connection_state(const char* value) {
    std::lock_guard<std::mutex> guard(output_mutex);
    std::cout << "STATE\t" << value << std::endl;
}

std::wstring credential_target(const std::string& app_id) {
    return L"PAFPlayer/DiscordSocial/" + std::wstring(app_id.begin(), app_id.end());
}

struct Tokens {
    std::string access;
    std::string refresh;
    std::time_t expires_at = 0;
};

std::optional<Tokens> read_tokens(const std::string& app_id) {
    PCREDENTIALW value = nullptr;
    const auto target = credential_target(app_id);
    if (!CredReadW(target.c_str(), CRED_TYPE_GENERIC, 0, &value)) return std::nullopt;
    std::string payload(reinterpret_cast<const char*>(value->CredentialBlob), value->CredentialBlobSize);
    CredFree(value);
    const auto first = payload.find('\n');
    const auto second = first == std::string::npos ? first : payload.find('\n', first + 1);
    if (first == std::string::npos || second == std::string::npos) return std::nullopt;
    try {
        Tokens tokens{payload.substr(0, first), payload.substr(first + 1, second - first - 1),
                      static_cast<std::time_t>(std::stoll(payload.substr(second + 1)))};
        if (tokens.access.empty() || tokens.refresh.empty()) return std::nullopt;
        return tokens;
    } catch (const std::exception&) { return std::nullopt; }
}

bool write_tokens(const std::string& app_id, const Tokens& tokens) {
    const auto target = credential_target(app_id);
    const std::string payload = tokens.access + '\n' + tokens.refresh + '\n' + std::to_string(tokens.expires_at);
    CREDENTIALW value{};
    value.Type = CRED_TYPE_GENERIC;
    value.TargetName = const_cast<LPWSTR>(target.c_str());
    value.CredentialBlobSize = static_cast<DWORD>(payload.size());
    value.CredentialBlob = reinterpret_cast<LPBYTE>(const_cast<char*>(payload.data()));
    value.Persist = CRED_PERSIST_LOCAL_MACHINE;
    value.UserName = const_cast<LPWSTR>(L"PAFPlayer Discord Social SDK");
    return CredWriteW(&value, 0) != 0;
}

std::string decode_base64(std::string_view input) {
    constexpr std::string_view alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string output;
    int bits = 0, count = -8;
    for (char c : input) {
        if (c == '=') break;
        const auto index = alphabet.find(c);
        if (index == std::string_view::npos) throw std::invalid_argument("Invalid encoded activity");
        bits = (bits << 6) | static_cast<int>(index);
        count += 6;
        if (count >= 0) {
            output.push_back(static_cast<char>((bits >> count) & 0xff));
            count -= 8;
        }
    }
    return output;
}

std::vector<std::string> split_tabs(const std::string& line) {
    std::vector<std::string> fields;
    std::size_t start = 0, at;
    while ((at = line.find('\t', start)) != std::string::npos) {
        fields.push_back(line.substr(start, at - start)); start = at + 1;
    }
    fields.push_back(line.substr(start));
    return fields;
}

class Bridge {
public:
    explicit Bridge(std::string app_id)
        : app_id_(std::move(app_id)), numeric_id_(std::stoull(app_id_)),
          client_(std::make_shared<discordpp::Client>()) {
        client_->SetStatusChangedCallback([this](discordpp::Client::Status state,
                                                  discordpp::Client::Error error, int32_t) {
            ready_ = state == discordpp::Client::Status::Ready;
            if (ready_) { connection_state("READY"); status("Connected to Discord without Desktop"); publish(); }
            else {
                connection_state("DISCONNECTED");
                if (error != discordpp::Client::Error::None) status("Discord connection failed; reconnecting");
            }
        });
        const auto saved = read_tokens(app_id_);
        if (saved) {
            tokens_ = *saved;
            refresh();
        } else {
            connection_state("AUTH_REQUIRED");
            status("Connect your Discord account in PAFPlayer Web Config");
        }
    }

    void run() {
        auto input = input_;
        std::thread([input] {
            std::string line;
            while (std::getline(std::cin, line)) {
                if (line.size() > 4096) continue;
                std::lock_guard<std::mutex> guard(input->mutex);
                input->commands.push(std::move(line));
            }
            std::lock_guard<std::mutex> guard(input->mutex);
            input->commands.push("STOP");
        }).detach();
        while (running_) {
            std::queue<std::string> incoming;
            {
                std::lock_guard<std::mutex> guard(input_->mutex);
                incoming.swap(input_->commands);
            }
            while (!incoming.empty()) {
                handle(incoming.front()); incoming.pop();
            }
            discordpp::RunCallbacks();
            if (tokens_ && !refreshing_ && std::chrono::steady_clock::now() >= next_refresh_attempt_ &&
                (!ready_ || std::time(nullptr) + 300 >= tokens_->expires_at))
                refresh();
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
        if (ready_ && published_) {
            client_->ClearRichPresence();
            for (int i = 0; i < 20; ++i) {
                discordpp::RunCallbacks();
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        }
        client_->Disconnect();
    }

private:
    void handle(const std::string& line) {
        const auto fields = split_tabs(line);
        if (fields[0] == "STOP") { running_ = false; return; }
        if (fields[0] == "AUTHORIZE") { authorize(); return; }
        if (fields[0] == "FORGET") {
            ++auth_epoch_;
            const auto target = credential_target(app_id_);
            CredDeleteW(target.c_str(), CRED_TYPE_GENERIC, 0);
            tokens_.reset(); refreshing_ = false; pending_clear_ = true; have_pending_ = true;
            if (ready_ && published_) client_->ClearRichPresence();
            published_ = false;
            client_->Disconnect(); ready_ = false;
            connection_state("AUTH_REQUIRED");
            status("Local Discord authorization removed"); return;
        }
        if (fields[0] == "CLEAR") {
            pending_clear_ = true; have_pending_ = true; publish(); return;
        }
        if (fields[0] == "SET" && (fields.size() == 3 || fields.size() == 5)) {
            try {
                details_ = decode_base64(fields[1]); state_ = decode_base64(fields[2]);
                image_ = fields.size() == 5 ? decode_base64(fields[3]) : "";
                image_text_ = fields.size() == 5 ? decode_base64(fields[4]) : "";
                pending_clear_ = false; have_pending_ = true; publish();
            } catch (const std::invalid_argument&) { status("Invalid activity update rejected"); }
        }
    }

    void authorize() {
        connection_state("AUTHORIZING");
        status("Opening Discord account authorization");
        const auto epoch = ++auth_epoch_;
        auto verifier = client_->CreateAuthorizationCodeVerifier();
        discordpp::AuthorizationArgs args{};
        args.SetClientId(numeric_id_);
        args.SetScopes(discordpp::Client::GetDefaultPresenceScopes());
        args.SetCodeChallenge(verifier.Challenge());
        client_->Authorize(args, [this, verifier, epoch](discordpp::ClientResult result,
                                                  std::string code, std::string redirect_uri) {
            if (epoch != auth_epoch_) return;
            if (!result.Successful()) {
                connection_state("AUTH_REQUIRED");
                status("Discord authorization was cancelled or failed"); return;
            }
            client_->GetToken(numeric_id_, code, verifier.Verifier(), redirect_uri,
                [this, epoch](discordpp::ClientResult exchange, std::string access, std::string refresh,
                       discordpp::AuthorizationTokenType, int32_t expires_in, std::string) {
                    if (epoch != auth_epoch_) return;
                    if (!exchange.Successful()) {
                        connection_state("AUTH_REQUIRED");
                        status("Discord token exchange failed"); return;
                    }
                    accept_tokens(std::move(access), std::move(refresh), expires_in);
                });
        });
    }

    void refresh() {
        if (!tokens_ || refreshing_) return;
        refreshing_ = true;
        next_refresh_attempt_ = std::chrono::steady_clock::now() + std::chrono::seconds(30);
        const auto epoch = auth_epoch_;
        client_->RefreshToken(numeric_id_, tokens_->refresh,
            [this, epoch](discordpp::ClientResult result, std::string access, std::string refresh,
                   discordpp::AuthorizationTokenType, int32_t expires_in, std::string) {
                refreshing_ = false;
                if (epoch != auth_epoch_) return;
                if (!result.Successful()) {
                    status("Discord token refresh failed; retrying without erasing authorization");
                    return;
                }
                accept_tokens(std::move(access), std::move(refresh), expires_in);
            });
    }

    void accept_tokens(std::string access, std::string refresh, int32_t expires_in) {
        tokens_ = Tokens{std::move(access), std::move(refresh),
                         std::time(nullptr) + std::max<int32_t>(expires_in, 60)};
        if (!write_tokens(app_id_, *tokens_))
            status("Discord connected, but Windows Credential Manager could not save authorization");
        const auto epoch = auth_epoch_;
        client_->UpdateToken(discordpp::AuthorizationTokenType::Bearer, tokens_->access,
            [this, epoch](discordpp::ClientResult result) {
                if (epoch != auth_epoch_) return;
                if (!result.Successful()) { connection_state("DISCONNECTED"); status("Discord rejected the account token"); return; }
                if (!ready_) client_->Connect();
            });
    }

    void publish() {
        if (!ready_ || !have_pending_) return;
        if (pending_clear_) {
            if (published_) client_->ClearRichPresence();
            published_ = false;
            status("Discord profile activity cleared"); return;
        }
        discordpp::Activity activity;
        activity.SetType(discordpp::ActivityTypes::Listening);
        activity.SetDetails(details_);
        activity.SetState(state_);
        if (!image_.empty()) {
            discordpp::ActivityAssets assets;
            assets.SetLargeImage(image_);
            if (!image_text_.empty()) assets.SetLargeText(image_text_);
            activity.SetAssets(assets);
        }
        published_ = true;
        client_->UpdateRichPresence(activity, [](discordpp::ClientResult result) {
            status(result.Successful() ? "Discord profile activity updated" : "Discord profile update failed");
        });
    }

    std::string app_id_, details_, state_, image_, image_text_;
    uint64_t numeric_id_;
    std::shared_ptr<discordpp::Client> client_;
    std::optional<Tokens> tokens_;
    std::chrono::steady_clock::time_point next_refresh_attempt_ = std::chrono::steady_clock::time_point::min();
    struct InputQueue { std::mutex mutex; std::queue<std::string> commands; };
    std::shared_ptr<InputQueue> input_ = std::make_shared<InputQueue>();
    uint64_t auth_epoch_ = 0;
    bool running_ = true, ready_ = false, refreshing_ = false;
    bool have_pending_ = false, pending_clear_ = true, published_ = false;
};
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string app_id = argv[1];
    if (app_id.size() < 17 || app_id.size() > 20 ||
        !std::all_of(app_id.begin(), app_id.end(), [](unsigned char c) { return c >= '0' && c <= '9'; })) return 2;
    try { Bridge(app_id).run(); return 0; }
    catch (const std::exception&) { status("Discord Social SDK helper could not start"); return 1; }
}
