cmake_minimum_required(VERSION 3.16)
project(PAFPlayerDiscordSocial LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT WIN32)
  message(FATAL_ERROR "PAFPlayer's Discord Social SDK helper is Windows-only")
endif()

set(DISCORD_SDK_ROOT "" CACHE PATH "Extracted official Discord Social SDK C++ directory")
if(NOT EXISTS "${DISCORD_SDK_ROOT}/include/discordpp.h")
  message(FATAL_ERROR "Set DISCORD_SDK_ROOT to the official Discord Social SDK C++ extraction")
endif()

set(DISCORD_SDK_LIB "${DISCORD_SDK_ROOT}/lib/release/discord_partner_sdk.lib")
set(DISCORD_SDK_DLL "${DISCORD_SDK_ROOT}/bin/release/discord_partner_sdk.dll")
if(NOT EXISTS "${DISCORD_SDK_LIB}" OR NOT EXISTS "${DISCORD_SDK_DLL}")
  message(FATAL_ERROR "The official Windows Social SDK .lib and .dll are required")
endif()

add_executable(PAFPlayerDiscordSocial PAFPlayerDiscordSocial.cpp)
target_include_directories(PAFPlayerDiscordSocial PRIVATE "${DISCORD_SDK_ROOT}/include")
target_link_libraries(PAFPlayerDiscordSocial PRIVATE "${DISCORD_SDK_LIB}" advapi32)
set_target_properties(PAFPlayerDiscordSocial PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
add_custom_command(TARGET PAFPlayerDiscordSocial POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
          "${DISCORD_SDK_DLL}" "${CMAKE_CURRENT_SOURCE_DIR}/discord_partner_sdk.dll")
