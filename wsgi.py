<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Logo Vote · LTC Fund Swift Capital Call{% endblock %}</title>
  <link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
        :root{
      --green:#184224; --green-deep:#0E2E18; --gold:#B48418; --gold-soft:#C9A24A;
      --ink:#16231B; --slate:#5C6B62; --paper:#F6F4EF; --paper-2:#ECE7DC; --line:#DED8CB; --white:#FFFFFF;
    }
    *{box-sizing:border-box;}
    body{
      margin:0; color:var(--ink); font-family:"Hanken Grotesk",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      line-height:1.55; -webkit-font-smoothing:antialiased;
      background:
        radial-gradient(1100px 480px at 85% -10%, rgba(24,66,36,.06), transparent 60%),
        radial-gradient(900px 480px at -5% 110%, rgba(180,132,24,.08), transparent 55%),
        var(--paper);
      min-height:100vh;
    }
    .lv-shell{max-width:1000px; margin:0 auto; padding:clamp(20px,4vw,48px);}
    .flash{border-radius:12px; padding:12px 16px; margin:0 0 14px; font-size:.9rem; border:1px solid var(--line);}
    .flash.success{background:#eaf6f3; border-color:#bfe3da; color:#0a5c50;}
    .flash.warning{background:#fdf6e7; border-color:#eedbb0; color:#8a6d1f;}
    .flash.info{background:#eef3f5; border-color:#d6e0e3; color:#3a4a52;}
    a{color:var(--green);}
  </style>
</head>
<body>
  <div class="lv-shell">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
</body>
</html>
