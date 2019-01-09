<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>{{ html.get("page_title", "Change password") }}</title>
    <link rel="stylesheet" href="{{ url("static", filename="style.css") }}">
    <script>
      % import json
      var policy = {{! json.dumps(dict(policy)) }};
    </script>
    <script src="{{ url("static", filename="scripts.js") }}"></script>
  </head>

  <body onload="check_password();">
    <main>
      <h1>{{ html.get("page_title", "Change password") }}</h1>

      <div class="alerts">
        % for type, text in get('alerts', []):
          <div class="alert {{ type }}">{{ text }}</div>
        % end
      </div>

      <form method="post" onsubmit="return check_password()">
        <label for="username">Username</label>
        <input id="username" name="username" value="{{ get("username", "") }}" type="text" required autofocus oninput="check_password()">

        <label for="old-password">Old password</label>
        <input id="old_password" name="old_password" type="password" required oninput="check_password()">

        <label for="new_password">New password</label>
        <input id="new_password" name="new_password" type="password" required oninput="check_password()">

        % if policy:
          <div id="policy_fulfilled" class="alert success">
            This password is suitable.
          </div>
          <div id="policy_unfulfilled" class="alert error policy">
            Requirements for your new password:
            <ul>
              % if policy["min_length"]:
                <li id="policy_li_min_length">
                  at least {{ policy["min_length"] }} character(s) long
                </li>
              % end
              % if policy["max_length"]:
                <li id="policy_li_max_length">
                  not more than {{ policy["max_length"] }} character(s) long
                </li>
              % end
              % if policy["min_lowers"]:
                <li id="policy_li_min_lowers">
                  at least {{ policy["min_lowers"] }} lowercase character(s)
                </li>
              % end
              % if policy["min_uppers"]:
                <li id="policy_li_min_uppers">
                  at least {{ policy["min_uppers"] }} uppercase character(s)
                </li>
              % end
              % if policy["min_digits"]:
                <li id="policy_li_min_digits">
                  at least {{ policy["min_digits"] }} digit(s)
                </li>
              % end
              % if policy["min_specials"]:
                <li id="policy_li_min_specials">
                  at least {{ policy["min_specials"] }} of the following characters
                  % specials = policy["specials"]
                  % if " " in specials:
                    % specials = specials.replace(" ", "")
                    (including space)
                  % end
                  <pre class="specials">{{ specials }}</pre>
                </li>
              % end
              % if policy["forbid_others"]:
                <li id="policy_li_forbid_others">
                  These characters are <strong>not allowed</strong>:
                  <pre id="policy_forbidden_chars" class="specials"></pre>
                </li>
              % end
              % if policy["forbid_username"]:
                <li id="policy_li_forbid_username">
                  Your password <strong>may not contain your username</strong>.
                </li>
              % end
              % if policy["forbid_reuse"]:
                <li id="policy_li_forbid_reuse">
                  You <strong>may not re-use</strong> your previous password.
                </li>
              % end
            </ul>
          </div>
        % end

        <label for="confirm_password">Confirm new password</label>
        <input id="confirm_password" name="confirm_password" type="password" required oninput="check_password()">

        <div id="confirmation_missmatch" class="alert warning">
          The two passwords don't match.
        </div>

        <button id="submit_btn" type="submit">Update password</button>
      </form>
    </main>
  </body>
</html>
