@Echo OFF
@on error cancel


rem Default tax rate:
        set TAX_RATE_PERCENT=6

rem Grab parameters:
        set PRICE=%1
        if "%2" != "" set TAX_RATE_PERCENT=%2


       
rem Validate environment (once):
        set validation_version=1
        iff "%validation_version%" != "%validated_tax%" then
                call validate-in-path math bigecho warning print-message
                call validate-environment-variables star TAX_RATE_PERCENT TAX_RATE_MULTIPLIER ansi_color_normal ansi_colors_have_been_set emoji_have_been_set EMOJI_HEAVY_DOLLAR_SIGN EMOJI_MONEY_WITH_WINGS EMOJI_MONEY_BAG EMOJI_MONEY_MOUTH_FACE
                if not defined percent call warning "percent env var must be defined so that ou can echo it and echo a percent symble"
                call validate-function rainbow
                set  validated_tax=%validation_version%
        endiff



rem If an argument was provided, use it to calculate, display, and copy result to clipboard:
        iff "%1" != "" then
                set TAX_RATE_MULTIPLIER=%@EVAL[1+(%TAX_RATE_PERCENT%/100)]
                set  taxed_price=%@EVAL[%@floor[%@EVAL[(%price * %TAX_RATE_MULTIPLIER + 0.005) * 100]]/100]
                echo.
                call bigecho %emoji_money_bag% %ansi_color_green%%EMOJI_HEAVY_DOLLAR_SIGN%%@rainbow[%1]  %ansi_color_normal%%faint%with%faint_off% %italics%%ansi_color_red%%TAX_RATE_PERCENT%%italics_off%%faint_on%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%percent%%ansi_color_normal%%faint_off% tax %faint_on%is%faint_off% %ansi_color_green%%EMOJI_HEAVY_DOLLAR_SIGN%%italics%%bold%%blink%%@rainbow[%taxed_price%]%underline_off%%italics_off%%blink_off%%bold_off%  %EMOJI_MONEY_MOUTH_FACE% %EMOJI_MONEY_WITH_WINGS%%EMOJI_MONEY_WITH_WINGS%%EMOJI_MONEY_WITH_WINGS%
                echo $%taxed_price%>clip:
        else
                echo %STAR% Must provide a price to calculate the tax of, at a default tax rate of %tax_rate_percent% percent, or specify a percentage as a second argument, e.g. %lq%display-tax-cost 99.99 10.5%rq% to display $99.99 at a 10.5 percent tax rate!
        endiff


