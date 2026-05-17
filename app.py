import os
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlparse

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, request, render_template_string, session, url_for
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
visitors = []

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "visitor_logs")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI")
facebook_login_enabled = bool(FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET)

oauth = OAuth(app)

if facebook_login_enabled:
    oauth.register(
        name="facebook",
        client_id=FACEBOOK_CLIENT_ID,
        client_secret=FACEBOOK_CLIENT_SECRET,
        access_token_url="https://graph.facebook.com/v19.0/oauth/access_token",
        authorize_url="https://www.facebook.com/v19.0/dialog/oauth",
        api_base_url="https://graph.facebook.com/v19.0/",
        client_kwargs={"scope": "email public_profile"},
    )

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Device Check</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>

        *{
            margin:0;
            padding:0;
            box-sizing:border-box;
        }

        body{
            font-family:Arial,sans-serif;
            min-height:100vh;
            background:linear-gradient(135deg,#0f172a,#2563eb,#7c3aed);
            display:flex;
            justify-content:center;
            align-items:center;
            overflow:hidden;
            color:white;
        }

        .bg{
            position:absolute;
            width:100%;
            height:100%;
            overflow:hidden;
            z-index:0;
        }

        .circle{
            position:absolute;
            border-radius:50%;
            background:rgba(255,255,255,0.08);
            animation:float 12s infinite linear;
        }

        .circle:nth-child(1){
            width:250px;
            height:250px;
            top:-60px;
            left:-60px;
        }

        .circle:nth-child(2){
            width:180px;
            height:180px;
            bottom:-40px;
            right:-30px;
        }

        .circle:nth-child(3){
            width:120px;
            height:120px;
            top:50%;
            left:10%;
        }

        @keyframes float{
            0%{
                transform:translateY(0px);
            }
            50%{
                transform:translateY(-20px);
            }
            100%{
                transform:translateY(0px);
            }
        }

        .card{
            position:relative;
            z-index:2;
            width:90%;
            max-width:430px;
            padding:35px;
            border-radius:28px;
            background:rgba(255,255,255,0.12);
            backdrop-filter:blur(15px);
            box-shadow:0 25px 60px rgba(0,0,0,0.4);
            text-align:center;
        }

        .icon{
            font-size:65px;
            margin-bottom:10px;
        }

        h1{
            font-size:30px;
            margin-bottom:10px;
        }

        p{
            color:#dbeafe;
            line-height:1.7;
        }

        .loader{
            width:65px;
            height:65px;
            border:5px solid rgba(255,255,255,0.2);
            border-top:5px solid white;
            border-radius:50%;
            margin:25px auto;
            animation:spin 1s linear infinite;
        }

        @keyframes spin{
            100%{
                transform:rotate(360deg);
            }
        }

        .badge{
            display:inline-block;
            padding:12px 22px;
            background:white;
            color:#2563eb;
            border-radius:999px;
            font-weight:bold;
            margin-top:10px;
        }

        .notice{
            margin-top:18px;
            font-size:13px;
            color:#bfdbfe;
        }

        form{
            margin-top:24px;
            display:grid;
            gap:12px;
        }

        input{
            width:100%;
            border:1px solid rgba(255,255,255,0.22);
            border-radius:14px;
            padding:14px 16px;
            background:rgba(15,23,42,0.55);
            color:white;
            font-size:15px;
            outline:none;
        }

        input::placeholder{
            color:#bfdbfe;
        }

        button{
            border:0;
            border-radius:14px;
            padding:14px 16px;
            background:white;
            color:#2563eb;
            font-size:15px;
            font-weight:bold;
            cursor:pointer;
        }

        button:disabled{
            cursor:not-allowed;
            opacity:0.65;
        }

        .login-button{
            display:block;
            margin-top:24px;
            border:0;
            border-radius:14px;
            padding:14px 16px;
            background:#1877f2;
            color:white;
            font-size:15px;
            font-weight:bold;
            text-decoration:none;
        }

        .profile{
            margin-top:18px;
            padding:14px;
            border-radius:14px;
            background:rgba(15,23,42,0.42);
            color:#dbeafe;
            font-size:13px;
        }

        .profile a{
            color:white;
        }

        .status{
            min-height:20px;
            color:#dbeafe;
            font-size:13px;
        }

    </style>

</head>

<body>

    <div class="bg">
        <div class="circle"></div>
        <div class="circle"></div>
        <div class="circle"></div>
    </div>

    <div class="card">

        <div class="icon">📱</div>

        <h1>Compatibility Check</h1>

        {% if facebook_user %}
        <p>
            Enter a Facebook profile or page URL to check device compatibility.
        </p>

        <div class="profile">
            Logged in as {{ facebook_user.get("name", "Facebook user") }}
            <br>
            <a href="/logout">Log out</a>
        </div>

        <form id="check-form">
            <input
                id="facebook-url"
                type="url"
                placeholder="https://www.facebook.com/username"
                required
            >

            <button id="submit-button" type="submit">
                Check Device
            </button>

            <div class="status" id="status"></div>
        </form>

        <div class="notice">
            Device details are recorded when you submit this form.
        </div>
        {% elif facebook_login_enabled %}
        <p>
            Log in with Facebook before submitting a device check.
        </p>

        <a class="login-button" href="/login/facebook">
            Continue with Facebook
        </a>

        <div class="notice">
            Facebook only shares profile details that you approve.
        </div>
        {% else %}
        <p>
            Facebook login is not configured yet.
        </p>

        <div class="notice">
            Add FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET, and FLASK_SECRET_KEY in Vercel.
        </div>
        {% endif %}

    </div>

{% if facebook_user %}
<script>

function detectPlatform(){
    const userAgent = navigator.userAgent || "";
    const platform = navigator.platform || "";
    const lowerUserAgent = userAgent.toLowerCase();
    const lowerPlatform = platform.toLowerCase();

    if(lowerUserAgent.includes("android")){
        return "Android";
    }

    if(/iphone|ipod/.test(lowerUserAgent)){
        return "iPhone";
    }

    if(lowerUserAgent.includes("ipad") || (lowerPlatform === "macintel" && navigator.maxTouchPoints > 1)){
        return "iPad";
    }

    if(lowerPlatform.includes("win")){
        return "Windows";
    }

    if(lowerPlatform.includes("mac")){
        return "macOS";
    }

    if(lowerPlatform.includes("linux")){
        return "Linux";
    }

    return platform || "Unknown";
}

document.getElementById("check-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const status = document.getElementById("status");
    const submitButton = document.getElementById("submit-button");
    const facebookUrl = document.getElementById("facebook-url").value.trim();

    submitButton.disabled = true;
    status.textContent = "Checking device...";

    try{
        const response = await fetch("/collect",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                fbUrl:facebookUrl,
                userAgent:navigator.userAgent,
                platform:detectPlatform(),
                language:navigator.language,
                screen:screen.width + "x" + screen.height,
                timezone:Intl.DateTimeFormat().resolvedOptions().timeZone

            })

        });

        if(!response.ok){
            throw new Error("Request failed");
        }

        status.textContent = "Device check saved.";
    }catch(error){
        status.textContent = "Unable to save. Please check the URL and try again.";
    }finally{
        submitButton.disabled = false;
    }
});

</script>
{% endif %}

</body>
</html>
"""

ADMIN = """
<!DOCTYPE html>
<html>
<head>

<title>Admin Logs</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

body{
    font-family:Arial,sans-serif;
    background:#0f172a;
    color:white;
    padding:30px;
}

h1{
    margin-bottom:25px;
}

.log{
    background:#111827;
    padding:22px;
    border-radius:20px;
    margin-bottom:20px;
    border:1px solid rgba(255,255,255,0.08);
    box-shadow:0 10px 30px rgba(0,0,0,0.3);
}

.label{
    color:#60a5fa;
    font-weight:bold;
}

.empty{
    background:#111827;
    padding:30px;
    border-radius:20px;
}

</style>

</head>

<body>

<h1>Visitor Logs</h1>

{{ logs }}

</body>
</html>
"""

LEGAL_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>{{ title }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{
    font-family:Arial,sans-serif;
    max-width:760px;
    margin:0 auto;
    padding:40px 22px;
    color:#111827;
    line-height:1.7;
}
h1{
    line-height:1.2;
}
a{
    color:#2563eb;
}
</style>
</head>
<body>
{{ body }}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(
        PAGE,
        facebook_login_enabled=facebook_login_enabled,
        facebook_user=session.get("facebook_user"),
    )

@app.route("/login/facebook")
def facebook_login():
    if not facebook_login_enabled:
        return "Facebook login is not configured.", 503

    redirect_uri = FACEBOOK_REDIRECT_URI or url_for("facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)

@app.route("/auth/facebook/callback")
def facebook_callback():
    if not facebook_login_enabled:
        return "Facebook login is not configured.", 503

    token = oauth.facebook.authorize_access_token()
    response = oauth.facebook.get("me?fields=id,name,email", token=token)
    profile = response.json()

    session["facebook_user"] = {
        "id": profile.get("id"),
        "name": profile.get("name"),
        "email": profile.get("email"),
    }

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("facebook_user", None)
    return redirect(url_for("home"))

@app.route("/privacy")
def privacy():
    body = """
    <h1>Privacy Policy</h1>
    <p>Device Check collects information submitted through the app, including Facebook profile details shared after login consent, Facebook URLs submitted by the user, browser/device information, IP address, language, screen size, timezone, and submission time.</p>
    <p>This information is used to provide device check logs and app administration records. We do not sell this information.</p>
    <p>To request deletion of your data, follow the instructions on the <a href="/data-deletion">data deletion page</a>.</p>
    """

    return render_template_string(LEGAL_PAGE, title="Privacy Policy", body=body)

@app.route("/data-deletion")
def data_deletion():
    body = """
    <h1>User Data Deletion</h1>
    <p>To request deletion of data collected by Device Check, send an email to jhamsteak019@gmail.com with the subject line "Device Check Data Deletion".</p>
    <p>Please include your Facebook account name or Facebook user ID if available, plus the approximate date you used the app. We will remove matching records from our visitor logs.</p>
    """

    return render_template_string(LEGAL_PAGE, title="User Data Deletion", body=body)

@app.route("/terms")
def terms():
    body = """
    <h1>Terms of Service</h1>
    <p>By using Device Check, you agree to submit only information that you are authorized to provide.</p>
    <p>The app may ask you to sign in with Facebook and may store profile details that Facebook shares after your consent, along with submitted Facebook URLs and device information.</p>
    <p>This service is provided for basic device check and logging purposes. Do not use it for unauthorized access, impersonation, or collection of another person's private information.</p>
    <p>If you do not agree with these terms, do not use the app.</p>
    """

    return render_template_string(LEGAL_PAGE, title="Terms of Service", body=body)

def is_facebook_url(value):
    parsed = urlparse(value or "")
    hostname = (parsed.hostname or "").lower()

    return parsed.scheme in {"http", "https"} and (
        hostname == "facebook.com" or
        hostname == "www.facebook.com" or
        hostname.endswith(".facebook.com") or
        hostname == "fb.com" or
        hostname.endswith(".fb.com")
    )

@app.route("/collect", methods=["POST"])
def collect():
    facebook_user = session.get("facebook_user")

    if not facebook_user:
        return {"status": "error", "message": "Facebook login is required."}, 401

    data = request.get_json(silent=True) or {}
    fb_url = (data.get("fbUrl") or "").strip()

    if fb_url and not is_facebook_url(fb_url):
        return {"status": "error", "message": "Only Facebook URLs are accepted."}, 400

    payload = {
        "fb_url": fb_url,
        "fb_user_id": facebook_user.get("id"),
        "fb_name": facebook_user.get("name"),
        "fb_email": facebook_user.get("email"),
        "user_agent": data.get("userAgent"),
        "platform": data.get("platform"),
        "language": data.get("language"),
        "screen": data.get("screen"),
        "timezone": data.get("timezone"),
        "ip": request.headers.get(
            "X-Forwarded-For",
            request.remote_addr
        ),
        "collected_at": datetime.now(timezone.utc).isoformat()
    }

    if supabase:
        try:
            supabase.table(SUPABASE_TABLE).insert(payload).execute()
        except Exception:
            fallback_payload = dict(payload)
            fallback_payload.pop("fb_url", None)
            fallback_payload.pop("fb_user_id", None)
            fallback_payload.pop("fb_name", None)
            fallback_payload.pop("fb_email", None)
            supabase.table(SUPABASE_TABLE).insert(fallback_payload).execute()
    else:
        visitors.append(payload)

    print(payload)

    return {"status":"saved"}

@app.route("/admin")
def admin():

    if supabase:
        response = (
            supabase.table(SUPABASE_TABLE)
            .select("*")
            .order("collected_at", desc=True)
            .limit(100)
            .execute()
        )
        logs_data = response.data or []
    else:
        logs_data = list(reversed(visitors))

    if not logs_data:

        logs = "<div class='empty'>No visitor logs yet.</div>"

    else:

        logs = ""

        for v in logs_data:

            logs += f"""

            <div class="log">

            <p><span class="label">Time:</span> {escape(str(v.get('collected_at', '')))}</p>

            <p><span class="label">Facebook URL:</span> {escape(str(v.get('fb_url', '')))}</p>

            <p><span class="label">Facebook Account:</span> {escape(str(v.get('fb_name', '')))}</p>

            <p><span class="label">Facebook ID:</span> {escape(str(v.get('fb_user_id', '')))}</p>

            <p><span class="label">Facebook Email:</span> {escape(str(v.get('fb_email', '')))}</p>

            <p><span class="label">IP:</span> {escape(str(v.get('ip', '')))}</p>

            <p><span class="label">Device:</span> {escape(str(v.get('user_agent', '')))}</p>

            <p><span class="label">Platform:</span> {escape(str(v.get('platform', '')))}</p>

            <p><span class="label">Screen:</span> {escape(str(v.get('screen', '')))}</p>

            <p><span class="label">Language:</span> {escape(str(v.get('language', '')))}</p>

            <p><span class="label">Timezone:</span> {escape(str(v.get('timezone', '')))}</p>

            </div>

            """

    return render_template_string(ADMIN, logs=logs)

app = app
