function mark_policy_fulfilled(name, fulfilled) {
  var li = document.getElementById("policy_li_" + name);
  if (li)
    li.style.display = fulfilled ? "none" : "block";
  return fulfilled;
}

function count_specials(str) {
  var num_specials = 0;
  for (var i = 0; i < str.length; i ++) {
    if (policy["specials"].indexOf(str.charAt(i)) != -1)
      num_specials ++;
  }
  return num_specials;
}


function policy_min_length(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "min_length",
    !policy["min_length"] ||
    new_pw.value.length >= policy["min_length"]
  );
}
function policy_max_length(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    !policy["max_length"] ||
    "max_length", new_pw.value.length <= policy["max_length"]
  );
}

function policy_lowers(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "min_lowers",
    !policy["min_lowers"] ||
    policy["min_lowers"] <= new_pw.value.length -
    new_pw.value.replace(/[a-z]/g, "").length
  );
}
function policy_uppers(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "min_uppers",
    !policy["min_uppers"] ||
    policy["min_uppers"] <= new_pw.value.length -
    new_pw.value.replace(/[A-Z]/g, "").length
  );
}
function policy_digits(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "min_digits",
    !policy["min_digits"] ||
    policy["min_digits"] <= new_pw.value.length -
    new_pw.value.replace(/[0-9]/g, "").length
  );
}
function policy_specials(username, old_pw, new_pw, new_pw_confirmation) {
  var num_specials = count_specials(new_pw.value);
  return mark_policy_fulfilled(
    "min_specials",
    !policy["min_specials"] || !policy["specials"] ||
    policy["min_specials"] <= num_specials
  );
}

function policy_forbid_others(username, old_pw, new_pw, new_pw_confirmation) {
  if (!policy["forbid_others"])
    return mark_policy_fulfilled("forbid_others", true);

  var forbidden = "";
  for (var i = 0; i < new_pw.value.length; i ++) {
    var c = new_pw.value.charAt(i);
    if (forbidden.indexOf(c) == -1 && c.replace(/[a-zA-Z0-9]/g, "").length != 0 &&
        count_specials(c) == 0)
      forbidden += c;
  }
  document.getElementById("policy_forbidden_chars").innerHTML = forbidden;

  return mark_policy_fulfilled(
    "forbid_others",
    forbidden.length == 0
  );
}
function policy_forbid_username(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "forbid_username",
    !policy["forbid_username"] || username.value.trim().length == 0 ||
    new_pw.value.toLowerCase().indexOf(username.value.trim().toLowerCase()) == -1
  );
}
function policy_forbid_reuse(username, old_pw, new_pw, new_pw_confirmation) {
  return mark_policy_fulfilled(
    "forbid_reuse",
    !policy["forbid_reuse"] || new_pw.value.length == 0 ||
    new_pw.value != old_pw.value
  );
}


function check_password() {
  var checks = [policy_min_length, policy_max_length,
                policy_lowers, policy_uppers, policy_digits, policy_specials,
                policy_forbid_others, policy_forbid_username, policy_forbid_reuse]

  var username = document.getElementById("username");
  var old_pw = document.getElementById("old_password");
  var new_pw = document.getElementById("new_password");
  var new_pw_confirmation = document.getElementById("confirm_password");

  var ok = true;
  if (policy) {
    var fulfilled = true;
    for (var i = 0; i < checks.length; i ++) {
      var check = checks[i];
      fulfilled = check(username, old_pw, new_pw, new_pw_confirmation) && fulfilled;
    }
    document.getElementById("policy_fulfilled").style.display = fulfilled ? "block" : "none";
    document.getElementById("policy_unfulfilled").style.display = fulfilled ? "none" : "block";
    ok = ok && fulfilled;
  } else {
    document.getElementById("policy_block").style.display = "none";
  }

  ok = ok && username.value.length != 0;
  ok = ok && old_pw.value.length != 0;
  var confirmation_empty = new_pw_confirmation.value.length == 0;
  ok = ok && !confirmation_empty;
  if (confirmation_empty || new_pw.value == new_pw_confirmation.value) {
    document.getElementById("confirmation_missmatch").style.display = "none";
  } else {
    document.getElementById("confirmation_missmatch").style.display = "block";
    ok = false;
  }

  document.getElementById("submit_btn").disabled = !ok;
  return ok;
}
