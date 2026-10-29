import re
from urllib.parse import urljoin
from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Server-Side Headers (Browser/DevTools ko inka koi pata nahi chalega)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# --- Pure Server-Side Embedded HTML/CSS Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamLink Resolver</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        body {
            min-height: 100vh;
            background: #090a0f;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(123, 34, 250, 0.22) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(0, 230, 118, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 50% 50%, rgba(0, 176, 255, 0.08) 0%, transparent 50%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #f1f5f9;
        }

        .glass-card {
            width: 100%;
            max-width: 650px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(25px) saturate(180%);
            -webkit-backdrop-filter: blur(25px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 28px;
            padding: 36px 30px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .header {
            text-align: center;
            margin-bottom: 26px;
        }

        .header .badge {
            display: inline-flex;
            align-items: center;
            padding: 5px 14px;
            background: rgba(123, 34, 250, 0.12);
            border: 1px solid rgba(123, 34, 250, 0.3);
            border-radius: 99px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #a855f7;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 12px;
        }

        .header h1 {
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            font-size: 0.88rem;
            color: #94a3b8;
            margin-top: 6px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }

        .input-box {
            width: 100%;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.25s ease;
        }

        .input-box:focus {
            border-color: #7B22FA;
            box-shadow: 0 0 20px rgba(123, 34, 250, 0.35);
            background: rgba(255, 255, 255, 0.06);
        }

        .btn-extract {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 16px;
            background: linear-gradient(135deg, #7B22FA 0%, #4f46e5 100%);
            color: #fff;
            font-size: 0.96rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(123, 34, 250, 0.35);
            transition: all 0.25s ease;
        }

        .btn-extract:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(123, 34, 250, 0.5);
        }

        .error-card {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.25);
            color: #fca5a5;
            padding: 14px;
            border-radius: 14px;
            font-size: 0.85rem;
            margin-top: 16px;
            text-align: center;
        }

        .result-box {
            margin-top: 24px;
            padding: 22px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 20px;
        }

        .result-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }

        .result-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .final-link-card {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 18px;
            border-radius: 16px;
            margin-bottom: 12px;
        }

        .final-label {
            font-size: 0.72rem;
            color: #34d399;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }

        .link-text {
            font-size: 0.88rem;
            color: #f1f5f9;
            word-break: break-all;
            margin-bottom: 14px;
            line-height: 1.4;
        }

        .btn-open {
            display: block;
            width: 100%;
            padding: 12px 14px;
            font-size: 0.88rem;
            font-weight: 600;
            border-radius: 12px;
            text-align: center;
            text-decoration: none;
            background: #10b981;
            color: #fff;
            transition: all 0.2s ease;
        }

        .btn-open:hover {
            background: #059669;
        }
    </style>
</head>
<body>

    <div class="glass-card">
        <div class="header">
            <div class="badge">Protected Server-Side Engine</div>
            <h1>Bypass & Downloader</h1>
            <p>Paste RareAnimes post, Multiquality, or Zipper URL</p>
        </div>

        <!-- Normal HTML Form: No Client-side Javascript/API exposed -->
        <form method="POST" action="/" class="input-group">
            <input type="text" name="url" class="input-box" placeholder="Paste link here..." value="{{ input_url or '' }}" required autocomplete="off">
            <button type="submit" class="btn-extract">Resolve Download Link</button>
        </form>

        {% if error %}
        <div class="error-card">{{ error }}</div>
        {% endif %}

        {% if result %}
        <div class="result-box">
            <div class="result-header">
                <span class="result-title">🎯 Ready to Download</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 6px;">{{ result.input_type }}</span>
            </div>

            <div class="final-link-card">
                <div class="final-label">Direct Target Link</div>
                <div class="link-text">{{ result.final_download_url }}</div>
                <a href="{{ result.final_download_url }}" target="_blank" rel="noopener noreferrer" class="btn-open">Open Download Link ↗</a>
            </div>
        </div>
        {% endif %}
    </div>

</body>
</html>
"""

# --- Server-Side Helper Functions ---
def extract_data_href(html_text, base_url):
    soup = BeautifulSoup(html_text, "html.parser")
    btn = soup.find("a", id="goBtn") or soup.find("a", attrs={"data-href": True})

    if btn and btn.get("data-href"):
        href = btn["data-href"].replace("&amp;", "&")
        return urljoin(base_url, href)

    match = re.search(r'data-href=["\']([^"\']+)["\']', html_text)
    if match:
        href = match.group(1).replace("&amp;", "&")
        return urljoin(base_url, href)

    return None

def extract_redirect_target(html_text):
    meta = re.search(r'content=["\']\d+;\s*URL=([^"\']+)["\']', html_text, re.IGNORECASE)
    if meta:
        return meta.group(1).replace("\\/", "/")

    js_loc = re.search(r'(?:location\.replace|location\.href\s*=)\s*\(?["\']([^"\']+)["\']\)?', html_text)
    if js_loc:
        url = js_loc.group(1).replace("\\/", "/")
        if "rareanimes.com/home" not in url:
            return url

    return None

def process_bypass(target_url):
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    chain = {
        "input_url": target_url,
        "input_type": None,
        "step2_zipper_url": None,
        "final_download_url": None
    }

    # Case 1: Direct Zipper Link
    if "codedew.com/zipper" in target_url:
        chain["input_type"] = "direct_zipper"
        if "ad_done=1" in target_url:
            chain["step2_zipper_url"] = target_url
            step2_referer = target_url.replace("&ad_done=1", "")
        else:
            session.headers["Referer"] = "https://codedew.com/"
            res_step1 = session.get(target_url, timeout=15)
            step2_url = extract_data_href(res_step1.text, target_url) or (target_url + "&ad_done=1")
            chain["step2_zipper_url"] = step2_url
            step2_referer = target_url

    # Case 2: Direct Multiquality Link
    elif "codedew.com/multiquality" in target_url:
        chain["input_type"] = "direct_multiquality"
        session.headers["Referer"] = "https://www.rareanimes.mov/"
        res_multi = session.get(target_url, allow_redirects=True, timeout=15)

        soup_mq = BeautifulSoup(res_multi.text, "html.parser")
        step1_url = None
        for a in soup_mq.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True).lower()
            if "codedew.com/zipper" in href or "download" in text:
                step1_url = urljoin(res_multi.url, href)
                break

        if not step1_url:
            raise Exception("Multiquality page par download button nahi mila.")

        session.headers["Referer"] = res_multi.url
        res_step1 = session.get(step1_url, timeout=15)
        step2_url = extract_data_href(res_step1.text, step1_url) or (step1_url + "&ad_done=1")
        chain["step2_zipper_url"] = step2_url
        step2_referer = step1_url

    # Case 3: Main Post Link
    else:
        chain["input_type"] = "main_post_page"
        session.headers["Referer"] = "https://www.google.com/"
        res_main = session.get(target_url, timeout=15)
        soup_main = BeautifulSoup(res_main.text, "html.parser")

        multi_node = soup_main.find("a", string=lambda t: t and "WatchMultiQuality" in t)
        if not multi_node:
            for a in soup_main.find_all("a", href=True):
                if "WatchMultiQuality" in a.text:
                    multi_node = a
                    break

        if not multi_node or not multi_node.get("href"):
            raise Exception("WatchMultiQuality button page par nahi mila.")

        watch_multi_url = multi_node["href"]
        session.headers["Referer"] = target_url
        res_multi = session.get(watch_multi_url, allow_redirects=True, timeout=15)

        soup_mq = BeautifulSoup(res_multi.text, "html.parser")
        step1_url = None
        for a in soup_mq.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True).lower()
            if "codedew.com/zipper" in href or "download" in text:
                step1_url = urljoin(res_multi.url, href)
                break

        if not step1_url:
            step1_url = watch_multi_url

        session.headers["Referer"] = res_multi.url
        res_step1 = session.get(step1_url, timeout=15)
        step2_url = extract_data_href(res_step1.text, step1_url) or (step1_url + "&ad_done=1")
        chain["step2_zipper_url"] = step2_url
        step2_referer = step1_url

    # Step 2 se CDN link (ziptron/liptron) extract karna
    session.headers["Referer"] = step2_referer
    res_step2 = session.get(chain["step2_zipper_url"], timeout=15)

    cdn_url = extract_data_href(res_step2.text, chain["step2_zipper_url"])
    if not cdn_url:
        cdn_match = re.search(
            r'https?://codedew\.com/cdn/(?:ziptron|liptron)\.php/\?[^"\'>\s]+',
            res_step2.text,
        )
        if cdn_match:
            cdn_url = cdn_match.group(0)

    if not cdn_url:
        raise Exception("CDN link node generate nahi ho saka.")

    # CDN Resolution
    session.headers["Referer"] = chain["step2_zipper_url"]
    res_cdn = session.get(cdn_url, allow_redirects=True, timeout=15)
    resolved_link = extract_redirect_target(res_cdn.text) or res_cdn.url

    if "rareanimes.com/home" in resolved_link:
        raise Exception("Security check failed (Session expired).")

    chain["final_download_url"] = resolved_link
    return chain

# --- Web Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    result = None
    input_url = None

    if request.method == "POST":
        input_url = request.form.get("url", "").strip()
        if not input_url:
            error = "Kripya ek valid URL enter karein."
        else:
            try:
                result = process_bypass(input_url)
            except Exception as e:
                error = str(e)

    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        result=result,
        input_url=input_url
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
