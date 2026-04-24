# Pro Tips

**Reuse State:** Once logged in, save the authentication state using `page.context.storage_state(path="auth.json")`. You can then load this file in future sessions to skip the login/OTP process entirely.

**Avoid Fixed Delays:** Never use `page.wait_for_timeout(5000)`. Instead, wait for specific URLs or elements to make your script faster and more reliable. 
