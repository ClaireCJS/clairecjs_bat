@Echo OFF
@on error cancel


rem Config:
        set TAX_RATE_MULTIPLIER=1.06
        set TAX_RATE_PERCENT=6
        set PRICE=%1


rem Validate environment (once):
        set validation_version=%@rainbow[asdfasdf]
        iff "%validation_version%" != "%validated_tax%" then
                call validate-in-path math bigecho warning print-message
                call validate-environment-variables star TAX_RATE_PERCENT TAX_RATE_MULTIPLIER ansi_color_normal ansi_colors_have_been_set emoji_have_been_set EMOJI_HEAVY_DOLLAR_SIGN EMOJI_MONEY_WITH_WINGS EMOJI_MONEY_BAG EMOJI_MONEY_MOUTH_FACE
                if not defined percent call warning "percent env var must be defined so that ou can echo it and echo a percent symble"
                call validate-function rainbow
                set  validated_tax=%validation_version%
        endiff



rem Calculate:
        iff "%1" != "" then
                set  taxed_price=%@EVAL[%@floor[%@EVAL[(%price * %TAX_RATE_MULTIPLIER + 0.005) * 100]]/100]
                echo.
                call bigecho %emoji_money_bag%  %ansi_color_green%%EMOJI_HEAVY_DOLLAR_SIGN%%@rainbow[%1]  %ansi_color_normal%with %TAX_RATE_PERCENT%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent% tax is %ansi_color_green%%EMOJI_HEAVY_DOLLAR_SIGN%%italics%%bold%%blink%%@rainbow[%taxed_price%]%underline_off%%italics_off%%blink_off%%bold_off%  %EMOJI_MONEY_MOUTH_FACE% %EMOJI_MONEY_WITH_WINGS%%EMOJI_MONEY_WITH_WINGS%%EMOJI_MONEY_WITH_WINGS%
        else
                echo %STAR% Must provide a price to calculate the tax of!
        endiff


