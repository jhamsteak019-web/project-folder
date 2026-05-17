from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)
visitors = []

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

        <p>
            Please wait while we verify your browser and device compatibility.
        </p>

        <div class="loader"></div>

        <div class="badge">
            Scanning Device...
        </div>

        <div class="notice">
            Basic browser analytics may be collected for performance and security purposes.
        </div>

    </div>

<script>

fetch("/collect",{

    method:"POST",

    headers:{
        "Content-Type":"application/json"
    },

    body:JSON.stringify({

        userAgent:navigator.userAgent,
        platform:navigator.platform,
        language:navigator.language,
        screen:screen.width + "x" + screen.height,
        timezone:Intl.DateTimeFormat().resolvedOptions().timeZone

    })

});

</script>

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

@app.route("/")
def home():
    return render_template_string(PAGE)

@app.route("/collect", methods=["POST"])
def collect():

    data = request.json

    data["ip"] = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    )

    data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    visitors.append(data)

    print(data)

    return {"status":"saved"}

@app.route("/admin")
def admin():

    if not visitors:

        logs = "<div class='empty'>No visitor logs yet.</div>"

    else:

        logs = ""

        for v in reversed(visitors):

            logs += f"""

            <div class="log">

            <p><span class="label">Time:</span> {v.get('time')}</p>

            <p><span class="label">IP:</span> {v.get('ip')}</p>

            <p><span class="label">Device:</span> {v.get('userAgent')}</p>

            <p><span class="label">Platform:</span> {v.get('platform')}</p>

            <p><span class="label">Screen:</span> {v.get('screen')}</p>

            <p><span class="label">Language:</span> {v.get('language')}</p>

            <p><span class="label">Timezone:</span> {v.get('timezone')}</p>

            </div>

            """

    return render_template_string(ADMIN, logs=logs)

app = app