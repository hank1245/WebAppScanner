# 파일 경로: app.py

import os
from flask import Flask, render_template, request, make_response, jsonify, send_from_directory

app = Flask(__name__)

# 업로드, 백업, 비밀 디렉터리 생성을 위한 설정
UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backup'
SECRET_FOLDER = 'secret'
CONFIG_FOLDER = 'config'
for folder in [UPLOAD_FOLDER, BACKUP_FOLDER, SECRET_FOLDER, CONFIG_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 테스트용 파일 생성
with open(os.path.join(UPLOAD_FOLDER, 'report.pdf'), 'w') as f:
    f.write('This is a test PDF report.')
with open(os.path.join(UPLOAD_FOLDER, 'image.png'), 'w') as f:
    f.write('This is a test PNG image.')
with open(os.path.join(BACKUP_FOLDER, 'backup_2024.zip'), 'w') as f:
    f.write('This is a test ZIP backup.')
with open(os.path.join(SECRET_FOLDER, 'private_key.txt'), 'w') as f:
    f.write('This is a secret key.')
with open(os.path.join(CONFIG_FOLDER, 'settings.conf'), 'w') as f:
    f.write('app_version=1.0')


@app.after_request
def add_custom_headers(response):
    """서버 정보 수집 테스트를 위해 Custom Header 추가"""
    response.headers['Server'] = 'Test-WebApp/1.0'
    response.headers['X-Powered-By'] = 'Test-Framework/1.1'
    return response

@app.route('/')
def index():
    """메인 페이지 - 크롤링 시작점"""
    return render_template('index.html')

@app.route('/about.html')
def about():
    """소개 페이지"""
    return render_template('about.html')

@app.route('/products/')
def products_index():
    """상품 목록 페이지"""
    return render_template('products/index.html')

@app.route('/products/item1.html')
def product_item1():
    """상품 상세 페이지 1"""
    return render_template('products/item1.html')

@app.route('/products/item2.html')
def product_item2():
    """상품 상세 페이지 2"""
    return render_template('products/item2.html')

@app.route('/login.html')
def login_page():
    """로그인 페이지 (쿠키 설정용)"""
    return render_template('login.html')

@app.route('/set-cookie')
def set_cookie():
    """세션 쿠키 설정 라우트"""
    resp = make_response("테스트용 세션 쿠키가 설정되었습니다. 이제 관리자 페이지에 접근해 보세요.")
    resp.set_cookie('session_id', 'loginsuccess')
    return resp

@app.route('/admin/dashboard.html')
def admin_dashboard():
    """관리자 대시보드 (쿠키 인증 필요)"""
    if request.cookies.get('session_id') == 'loginsuccess':
        return render_template('admin/dashboard.html')
    else:
        return "접근 권한이 없습니다. 먼저 로그인 해주세요.", 403

# robots.txt 파일 제공
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory('static', 'robots.txt')

# --- 디렉터리 리스팅 취약점 구현 ---
@app.route('/uploads/')
def list_uploads():
    """/uploads/ 디렉터리 리스팅"""
    files = os.listdir(UPLOAD_FOLDER)
    file_links = ''.join([f'<li><a href="/{UPLOAD_FOLDER}/{file}">{file}</a></li>' for file in files])
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Index of /{UPLOAD_FOLDER}/</title></head>
    <body>
    <h1>Index of /{UPLOAD_FOLDER}/</h1>
    <hr><pre><ul>
    {file_links}
    </ul></pre><hr>
    </body>
    </html>
    """
@app.route('/.well-known/<path:filename>')
def well_known_files(filename):
    return send_from_directory(os.path.join('static', '.well-known'), filename)


@app.route('/backup/')
def list_backup():
    """/backup/ 디렉터리 리스팅"""
    files = os.listdir(BACKUP_FOLDER)
    file_links = ''.join([f'<li><a href="/{BACKUP_FOLDER}/{file}">{file}</a></li>' for file in files])
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Index of /{BACKUP_FOLDER}/</title></head>
    <body>
    <h1>Index of /{BACKUP_FOLDER}/ (Parent Directory)</h1>
    <hr><pre><ul>
    {file_links}
    </ul></pre><hr>
    </body>
    </html>
    """

# --- 스캐너 제외 기능 테스트용 경로 ---
@app.route('/secret/')
def secret_dir():
    return "이곳은 robots.txt에 의해 접근이 제한되어야 합니다.", 200

@app.route('/config/')
def config_dir():
    return "이곳은 사용자의 제외 목록에 의해 스캔되지 않아야 합니다.", 200


# --- JS API 탐지 및 스캔 테스트용 API 엔드포인트 ---
@app.route('/api/v1/users')
def get_users():
    return jsonify([{'id': 1, 'name': 'testuser1'}, {'id': 2, 'name': 'testuser2'}])

@app.route('/api/v1/items')
def get_items():
    return jsonify([{'id': 101, 'item': 'test-item-1'}, {'id': 102, 'item': 'test-item-2'}])

# API 사전 스캔 테스트용
@app.route('/api/v1/orders/')
def get_orders():
    return "Orders API Endpoint Found", 200

@app.route('/api/v1/admin/')
def get_api_admin():
    return "API Admin Endpoint Found", 200


if __name__ == '__main__':
    # 디렉터리 경로를 명시적으로 지정
    template_dir = os.path.abspath('templates')
    static_dir = os.path.abspath('static')
    app.template_folder = template_dir
    app.static_folder = static_dir
    app.run(host='0.0.0.0', port=5001, debug=True)