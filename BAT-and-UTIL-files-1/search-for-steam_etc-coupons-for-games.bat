@Echo OFF
                set search_for=.
if "%1" ne "" ( set search_for=%*)

call warning "spaces need to be '%blink_on%+%blink_off%' tho, so maybe fix that:"
eset search_for

call warning "Don't bother searching Difmark - they are horrible scammers https://difmark.com/en/products?name=%search_for%"
pause               

    https://www.g2a.com/search?query=%search_for%
    https://www.gamersgate.com/games/?query=%search_for%
    https://www.eneba.com/us/store/all?text=%search_for%
    https://cdkeyprices.com/search?sk=%search_for%



