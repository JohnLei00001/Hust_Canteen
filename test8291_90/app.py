# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import uuid
import threading
import time
from functools import wraps
from safe_content_moderator import check_comment, check_text_safe, moderate_content, is_safe_comment
from security_utils import SecurityUtils
from security_middleware import SecurityMiddleware, SecurityLogger
from ddos_protection import ddos_protection, login_protection, rate_limit

app = Flask(__name__)
app.secret_key = 'helloworld'  # 生产环境请使用更安全的密钥
app.config['VERSION'] = '1.0.1'  # 版本号用于缓存清除
bcrypt = Bcrypt(app)

# 初始化安全组件
security_utils = SecurityUtils()
security_middleware = SecurityMiddleware(app)
security_logger = SecurityLogger()

# 添加安全中间件
security_middleware.init_app(app)

# 添加CORS支持，允许所有来源
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ray123_123',
    'database': 'hust_canteen'
}

def get_db_connection():
    """获取数据库连接，使用连接池和参数化查询"""
    return mysql.connector.connect(**db_config, pool_name="canteen_pool", pool_size=10)

# 登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 管理员装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('需要管理员权限', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 输入验证装饰器
def validate_form(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for field in required_fields:
                if field not in request.form:
                    flash(f'缺少必填字段: {field}', 'danger')
                    return redirect(request.referrer or url_for('dashboard'))
                
                # 验证输入长度和内容
                value = request.form[field]
                if len(value) > 255:  # 限制最大长度
                    flash(f'字段 {field} 过长', 'danger')
                    return redirect(request.referrer or url_for('dashboard'))
                
                # 过滤危险字符
                if re.search(r'[<>"\']', value):
                    flash(f'字段 {field} 包含非法字符', 'danger')
                    return redirect(request.referrer or url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=60)  # 每分钟最多5次登录尝试
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        # 获取客户端IP
        client_ip = request.remote_addr
        
        # 检查登录尝试限制
        if not login_protection.check_login_attempt(client_ip):
            flash('登录尝试过于频繁，请15分钟后再试', 'danger')
            security_logger.log_security_event('login_rate_limit', {
                'ip': client_ip,
                'username': username
            })
            return render_template('login.html')
        
        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('login.html')
        
        if len(username) > 50 or len(password) > 128:
            flash('输入过长', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 先检查普通用户表
            cursor.execute("SELECT * FROM anonymous_users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            # 如果普通用户表中没有，检查管理员表
            if not user:
                cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
                admin_user = cursor.fetchone()
                if admin_user and bcrypt.check_password_hash(admin_user['password_hash'], password):
                    # 管理员登录成功
                    login_protection.record_successful_login(client_ip)
                    
                    session['user_id'] = str(admin_user['id'])  # 使用管理员表ID
                    session['username'] = admin_user['username']
                    session['is_admin'] = True
                    session.pop('is_guest', None)
                    session['_login_version'] = '1.0'
                    
                    flash('管理员登录成功!', 'success')
                    security_logger.log_security_event('successful_admin_login', {
                        'user_id': admin_user['id'],
                        'username': username,
                        'ip': client_ip
                    })
                    
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('dashboard'))
            
            # 普通用户登录
            elif user and bcrypt.check_password_hash(user['password_hash'], password):
                # 登录成功，清除失败记录
                login_protection.record_successful_login(client_ip)
                
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['is_admin'] = user.get('is_admin', False)
                session.pop('is_guest', None)  # 清除访客模式标记
                session['_login_version'] = '1.0'  # 添加版本标识防止缓存
                
                # 更新最后登录时间
                cursor.execute("UPDATE anonymous_users SET last_login = %s WHERE user_id = %s",
                              (datetime.now(), user['user_id']))
                conn.commit()
                
                if remember:
                    session.permanent = True
                else:
                    session.permanent = False
                
                flash('登录成功!', 'success')
                security_logger.log_security_event('successful_login', {
                    'user_id': user['user_id'],
                    'username': username,
                    'ip': client_ip
                })
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                # 登录失败，记录尝试
                login_protection.record_failed_attempt(client_ip)
                flash('用户名或密码错误', 'danger')
                security_logger.log_security_event('failed_login', {
                    'ip': client_ip,
                    'username': username,
                    'attempts': len(login_protection.failed_attempts.get(client_ip, []))
                })
        except Exception as e:
            security_logger.log_security_event('login_error', {
                'error': str(e),
                'ip': client_ip,
                'username': username
            })
            flash('登录过程中发生错误', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        
        # 简单验证
        if len(username) < 3:
            flash('用户名至少需要3个字符', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('密码至少需要6个字符', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            user_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO anonymous_users (user_id, username, password_hash) VALUES (%s, %s, %s)",
                (user_id, username, password_hash)
            )
            conn.commit()
            flash('注册成功! 请登录', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:  # 重复键错误
                flash('用户名已被使用', 'danger')
            else:
                flash('注册失败: ' + str(err), 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/guest')
def guest_mode():
    session['user_id'] = 'guest_' + str(uuid.uuid4())
    session['username'] = '访客'
    session['is_guest'] = True
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dish/<int:dish_id>/reviews')
def dish_reviews_page(dish_id):
    return render_template('dish_reviews.html', dish_id=dish_id)

@app.route('/api/recommendations/<string:recommend_type>')
def api_recommendations(recommend_type):
    """
    分类推荐API：按类型返回推荐内容
    支持类型：dishes(菜品)、canteens(食堂)、stalls(窗口)、all(全部)
    优先级：食堂拥挤度低 → 窗口排队少 → 菜品评分高
    注意：降低条件确保有推荐数据
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    user_id = session.get('user_id')
    is_guest = session.get('is_guest', False)
    
    # 1. 推荐菜品：包含新菜品，给予基础曝光机会（优化：一次性查询收藏状态）
    dish_query = """
        SELECT d.dish_id AS id,
               sd.id AS stall_dish_id,
               d.name,
               cs.stall_id,
               COALESCE(cs.custom_name, st.name) AS stall_name,
               c.name AS canteen_name,
               COALESCE(d.avg_rating, 0) AS rating,
               sd.actual_price AS price,
               COALESCE(c.crowd_level, 3) AS canteen_crowd,
               COALESCE(cs.queue_rating, 3) AS stall_queue,
               'dish' AS type,
               -- 综合评分：新菜品给予基础分数，避免被埋没
               ((5 - COALESCE(c.crowd_level, 3)) * 2 + 
                (5 - COALESCE(cs.queue_rating, 3)) * 1.5 + 
                COALESCE(d.avg_rating, 2.5) * 3 + 
                CASE WHEN d.review_count = 0 THEN 2.0 ELSE 0 END) AS composite_score
    """
    
    if user_id and not is_guest:
        dish_query += """
            , CASE WHEN f.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
        """
    else:
        dish_query += """
            , 0 AS is_favorite
        """
    
    dish_query += """
        FROM dishes d
        JOIN stall_dishes sd ON d.dish_id = sd.dish_id
        JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
        JOIN stall_types st ON cs.type_id = st.type_id
        JOIN canteens c ON cs.canteen_id = c.canteen_id
    """
    
    if user_id and not is_guest:
        dish_query += """
            LEFT JOIN user_favorites f ON f.user_id = %s AND f.stall_dish_id = sd.id
        """
    
    dish_query += """
        WHERE sd.is_available = 1 
        ORDER BY composite_score DESC, d.review_count ASC, d.dish_id ASC
        LIMIT 10
    """
    
    if user_id and not is_guest:
        cur.execute(dish_query, (user_id,))
    else:
        cur.execute(dish_query)
    dishes = cur.fetchall()

    # 2. 推荐食堂：包含新食堂，给予基础曝光机会
    cur.execute("""
        SELECT c.canteen_id AS id,
               c.name,
               c.address,
               COALESCE(c.crowd_level, 3) AS rating,
               'canteen' AS type,
               (5 - COALESCE(c.crowd_level, 3)) AS comfort_score
        FROM canteens c
        ORDER BY comfort_score DESC, c.canteen_id ASC
        LIMIT 5
    """)
    canteens = cur.fetchall()

    # 3. 推荐窗口：包含新窗口，给予基础曝光机会
    cur.execute("""
        SELECT cs.stall_id AS id,
               COALESCE(cs.custom_name, st.name) AS name,
               c.name AS canteen_name,
               COALESCE(cs.queue_rating, 3) AS rating,
               'stall' AS type,
               (5 - COALESCE(cs.queue_rating, 3)) AS queue_score
        FROM canteen_stalls cs
        JOIN stall_types st ON cs.type_id = st.type_id
        JOIN canteens c ON cs.canteen_id = c.canteen_id
        ORDER BY queue_score DESC, cs.stall_id ASC
        LIMIT 5
    """)
    stalls = cur.fetchall()

    # 根据推荐类型返回对应数据
    result = []
    
    if recommend_type == 'dishes' or recommend_type == 'all':
        result.extend(dishes)
    
    if recommend_type == 'canteens' or recommend_type == 'all':
        result.extend(canteens)
    
    if recommend_type == 'stalls' or recommend_type == 'all':
        result.extend(stalls)
    
    # 如果指定了具体类型但结果为空，返回对应类型
    if recommend_type != 'all' and not result:
        return jsonify([])

    cur.close()
    conn.close()
    return jsonify(result)

@app.route('/api/rankings/<ranking_type>')
def api_rankings(ranking_type):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if ranking_type == 'top-rated':
        cur.execute("""
            SELECT d.dish_id AS id, d.name, 'dish' AS type,
                   d.avg_rating AS value, c.name AS location
            FROM dishes d
            JOIN stall_dishes sd ON d.dish_id = sd.dish_id
            JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
            JOIN canteens c ON cs.canteen_id = c.canteen_id
            WHERE sd.is_available = 1
            ORDER BY d.avg_rating DESC
            LIMIT 10
        """)
    elif ranking_type == 'most-popular':
        # 人气榜：按收藏人数排序
        cur.execute("""
            SELECT d.dish_id AS id, d.name, 'dish' AS type,
                   COALESCE(fav.favorite_count, 0) AS value, c.name AS location
            FROM dishes d
            JOIN stall_dishes sd ON d.dish_id = sd.dish_id
            JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
            JOIN canteens c ON cs.canteen_id = c.canteen_id
            LEFT JOIN (
                SELECT stall_dish_id, COUNT(*) as favorite_count
                FROM user_favorites
                GROUP BY stall_dish_id
            ) fav ON sd.id = fav.stall_dish_id
            WHERE sd.is_available = 1
            ORDER BY favorite_count DESC, d.dish_id
            LIMIT 10
        """)
    elif ranking_type == 'least-crowded':
        # 免排队榜：推荐人少的窗口
        cur.execute("""
            SELECT cs.stall_id AS id, 
                   COALESCE(cs.custom_name, st.name) AS name, 
                   'stall' AS type,
                   cs.queue_rating AS value, 
                   c.name AS location
            FROM canteen_stalls cs
            JOIN stall_types st ON cs.type_id = st.type_id
            JOIN canteens c ON cs.canteen_id = c.canteen_id
            WHERE cs.queue_rating IS NOT NULL 
                  AND cs.queue_rating > 0
            ORDER BY cs.queue_rating ASC
            LIMIT 10
        """)
    elif ranking_type == 'easy-seat':
        # 好找座：食堂空闲榜（原免排队榜）
        cur.execute("""
            SELECT c.canteen_id AS id, c.name, 'canteen' AS type,
                   c.crowd_level AS value, c.address AS location
            FROM canteens c
            WHERE c.crowd_level >= 0
            ORDER BY c.crowd_level ASC
            LIMIT 10
        """)
    elif ranking_type == 'join-fun':
        # 凑热闹：原人气榜，按评论数排序
        cur.execute("""
            SELECT d.dish_id AS id, d.name, 'dish' AS type,
                   d.review_count AS value, c.name AS location
            FROM dishes d
            JOIN stall_dishes sd ON d.dish_id = sd.dish_id
            JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
            JOIN canteens c ON cs.canteen_id = c.canteen_id
            WHERE sd.is_available = 1
            ORDER BY d.review_count DESC
            LIMIT 10
        """)
    else:
        return jsonify([])

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route('/api/canteen/<int:canteen_id>')
def api_canteen_detail(canteen_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, camp.name AS campus_name
        FROM canteens c
        JOIN campuses camp ON c.campus_id = camp.campus_id
        WHERE c.canteen_id = %s
    """, (canteen_id,))
    canteen = cur.fetchone()
    if not canteen:
        return jsonify({}), 404

    cur.execute("""
        SELECT cs.stall_id AS id,
               COALESCE(cs.custom_name, st.name) AS name,
               st.name AS type,
               cs.queue_rating
        FROM canteen_stalls cs
        JOIN stall_types st ON cs.type_id = st.type_id
        WHERE cs.canteen_id = %s
    """, (canteen_id,))
    canteen['stalls'] = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(canteen)

@app.route('/api/stall/<int:stall_id>')
def api_stall_detail(stall_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT cs.stall_id AS id,
               COALESCE(cs.custom_name, st.name) AS name,
               st.name AS type,
               cs.queue_rating,
               cs.queue_rating_count,
               c.name AS canteen,
               c.canteen_id
        FROM canteen_stalls cs
        JOIN stall_types st ON cs.type_id = st.type_id
        JOIN canteens c ON cs.canteen_id = c.canteen_id
        WHERE cs.stall_id = %s
    """, (stall_id,))
    stall = cur.fetchone()
    if not stall:
        return jsonify({}), 404

    cur.execute("""
        SELECT d.dish_id AS id, d.name, sd.actual_price AS price, d.avg_rating AS rating
        FROM stall_dishes sd
        JOIN dishes d ON sd.dish_id = d.dish_id
        WHERE sd.stall_id = %s AND sd.is_available = 1
    """, (stall_id,))
    stall['dishes'] = cur.fetchall()
    
    # 添加会话信息
    stall['session'] = {
        'user_id': session.get('user_id'),
        'is_guest': session.get('is_guest', False)
    }
    
    cur.close(); conn.close()
    return jsonify(stall)

@app.route('/api/dish/<int:dish_id>')
def api_dish_detail(dish_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM dishes WHERE dish_id = %s", (dish_id,))
    dish = cur.fetchone()
    if not dish:
        return jsonify({}), 404

    dish['session'] = {
        'user_id': session.get('user_id'),
        'is_guest': session.get('is_guest', False)
    }

    # 查询供应地点 - 保持不变
    cur.execute("""
        SELECT c.name AS canteen,
               COALESCE(cs.custom_name, st.name) AS stall,
               sd.actual_price AS price, 
               sd.is_available,
               cs.stall_id,
               sd.id AS stall_dish_id
        FROM stall_dishes sd
        JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
        JOIN stall_types st ON cs.type_id = st.type_id
        JOIN canteens c ON cs.canteen_id = c.canteen_id
        WHERE sd.dish_id = %s
    """, (dish_id,))
    dish['availability'] = cur.fetchall()

    # 修改评论查询：通过 stall_dishes 关联
    cur.execute("""
        SELECT r.rating, r.comment, r.created_at,
               u.username AS user
        FROM dish_reviews r
        JOIN anonymous_users u ON r.user_id = u.user_id
        JOIN stall_dishes sd ON r.stall_dish_id = sd.id
        WHERE sd.dish_id = %s
        ORDER BY r.created_at DESC
        LIMIT 20
    """, (dish_id,))
    dish['reviews'] = cur.fetchall()

    # 修改收藏状态判断：使用第一个可用档口菜品的 stall_dish_id
    user_id = session.get('user_id')
    if user_id and not session.get('is_guest') and dish['availability']:
        stall_dish_id = dish['availability'][0]['stall_dish_id']
        cur.execute("SELECT 1 FROM user_favorites WHERE user_id=%s AND stall_dish_id=%s", 
                   (user_id, stall_dish_id))
        dish['is_favorite'] = bool(cur.fetchone())
    else:
        dish['is_favorite'] = False
    
    cur.close(); conn.close()
    return jsonify(dish)

@app.route('/api/stall-dish/<int:stall_dish_id>')
def api_stall_dish_detail(stall_dish_id):
    """通过 stall_dish_id 获取唯一菜品详情"""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 获取菜品基本信息
    cur.execute("""
        SELECT d.dish_id, d.name, d.description, d.avg_rating, d.review_count,
               sd.id AS stall_dish_id, sd.actual_price AS price,
               c.name AS canteen, cs.stall_id,
               COALESCE(cs.custom_name, st.name) AS stall
        FROM stall_dishes sd
        JOIN dishes d ON sd.dish_id = d.dish_id
        JOIN canteen_stalls cs ON sd.stall_id = cs.stall_id
        JOIN stall_types st ON cs.type_id = st.type_id
        JOIN canteens c ON cs.canteen_id = c.canteen_id
        WHERE sd.id = %s AND sd.is_available = 1
    """, (stall_dish_id,))
    
    dish = cur.fetchone()
    if not dish:
        return jsonify({}), 404

    dish['session'] = {
        'user_id': session.get('user_id'),
        'is_guest': session.get('is_guest', False)
    }

    # 查询供应地点（只有一个）
    dish['availability'] = [{
        'canteen': dish['canteen'],
        'stall': dish['stall'],
        'price': dish['price'],
        'is_available': 1,
        'stall_id': dish['stall_id'],
        'stall_dish_id': stall_dish_id
    }]

    # 查询评论
    cur.execute("""
        SELECT r.rating, r.comment, r.created_at,
               u.username AS user
        FROM dish_reviews r
        JOIN anonymous_users u ON r.user_id = u.user_id
        WHERE r.stall_dish_id = %s
        ORDER BY r.created_at DESC
        LIMIT 20
    """, (stall_dish_id,))
    dish['reviews'] = cur.fetchall()

    # 查询收藏状态
    user_id = session.get('user_id')
    if user_id and not session.get('is_guest'):
        cur.execute("SELECT 1 FROM user_favorites WHERE user_id=%s AND stall_dish_id=%s", 
                   (user_id, stall_dish_id))
        dish['is_favorite'] = bool(cur.fetchone())
    else:
        dish['is_favorite'] = False

    cur.close(); conn.close()
    return jsonify(dish)

@app.route('/api/dish/<int:dish_id>/reviews')
def api_dish_reviews_all(dish_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    # 获取当前用户ID（用于判断点赞状态）
    current_user_id = session.get('user_id')
    
    # 新的查询：包含点赞数和点赞状态
    cur.execute("""
        SELECT r.review_id, r.rating, r.comment, r.created_at, r.like_count,
               u.username AS user, u.user_id,
               CASE WHEN cl.user_id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_user
        FROM dish_reviews r
        JOIN anonymous_users u ON r.user_id = u.user_id
        JOIN stall_dishes sd ON r.stall_dish_id = sd.id
        LEFT JOIN comment_likes cl ON r.review_id = cl.review_id AND cl.user_id = %s
        WHERE sd.dish_id = %s
        ORDER BY 
            -- 按权重排序：时效(30%) + 点赞(50%) + 评分(20%)
            (r.like_count * 0.5 + r.rating * 0.2 + 
             (1 - TIMESTAMPDIFF(HOUR, r.created_at, NOW()) / 168) * 0.3) DESC,
            r.created_at DESC
    """, (current_user_id, dish_id))
    
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({'dish_id': dish_id, 'reviews': data})

@app.route('/api/review', methods=['POST'])
def api_add_review():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401

    try:
        data = request.get_json()
        stall_dish_id = data.get('stall_dish_id')
        rating = int(data.get('rating'))
        comment = data.get('comment', '').strip()

        if not stall_dish_id or rating not in range(1, 6):
            return jsonify({'error': '参数错误'}), 400

        # 内容审核 - 如果有评论内容
        if comment:
            moderation_result = check_comment(comment)
            if not moderation_result['is_safe']:
                return jsonify({
                    'error': moderation_result['message'],
                    'violation_type': moderation_result['violation_type'],
                    'violation_words': moderation_result['violation_words']
                }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 获取 dish_id 和 stall_id
        cur.execute("SELECT dish_id, stall_id FROM stall_dishes WHERE id = %s", (stall_dish_id,))
        sd_data = cur.fetchone()
        if not sd_data:
            return jsonify({'error': '无效的档口菜品ID'}), 400
        dish_id, stall_id = sd_data  # 解包获取 dish_id 和 stall_id

        # 插入评论（包含 stall_id）
        cur.execute("""
            INSERT INTO dish_reviews
            (stall_dish_id, stall_id, user_id, rating, comment, like_count)
            VALUES (%s, %s, %s, %s, %s, 0)
        """, (stall_dish_id, stall_id, session['user_id'], rating, comment))
        
        # 更新菜品评分和评价数
        cur.execute("""
            UPDATE dishes
            SET avg_rating = COALESCE(
                    (SELECT AVG(rating) 
                     FROM dish_reviews dr
                     JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                     WHERE sd.dish_id = %s),
                    0
                ),
                review_count = (
                    SELECT COUNT(*) 
                    FROM dish_reviews dr
                    JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                    WHERE sd.dish_id = %s
                )
            WHERE dish_id = %s
        """, (dish_id, dish_id, dish_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/review/<int:review_id>/like', methods=['POST'])
def toggle_review_like(review_id):
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 检查是否已点赞
        cur.execute("""
            SELECT like_id FROM comment_likes 
            WHERE review_id = %s AND user_id = %s
        """, (review_id, session['user_id']))
        
        existing_like = cur.fetchone()
        
        if existing_like:
            # 取消点赞
            cur.execute("DELETE FROM comment_likes WHERE like_id = %s", (existing_like[0],))
            cur.execute("""
                UPDATE dish_reviews 
                SET like_count = like_count - 1 
                WHERE review_id = %s AND like_count > 0
            """, (review_id,))
            action = 'unliked'
        else:
            # 添加点赞
            cur.execute("""
                INSERT INTO comment_likes (review_id, user_id) 
                VALUES (%s, %s)
            """, (review_id, session['user_id']))
            cur.execute("""
                UPDATE dish_reviews 
                SET like_count = like_count + 1 
                WHERE review_id = %s
            """, (review_id,))
            action = 'liked'
        
        # 获取最新点赞数
        cur.execute("SELECT like_count FROM dish_reviews WHERE review_id = %s", (review_id,))
        new_count = cur.fetchone()[0]
        
        conn.commit()
        return jsonify({'success': True, 'action': action, 'like_count': new_count})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close(); conn.close()

@app.route('/api/review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 检查是否是评论作者
        cur.execute("""
            SELECT user_id, stall_id FROM dish_reviews 
            WHERE review_id = %s
        """, (review_id,))
        
        review = cur.fetchone()
        if not review or review[0] != session['user_id']:
            return jsonify({'error': '无权删除此评论'}), 403
        
        stall_id = review[1]
        
        # 获取对应的菜品ID
        cur.execute("""
            SELECT d.dish_id 
            FROM dishes d
            JOIN stall_dishes sd ON d.dish_id = sd.dish_id
            WHERE sd.stall_id = %s
            LIMIT 1
        """, (stall_id,))
        dish_result = cur.fetchone()
        dish_id = dish_result[0] if dish_result else None
        
        # 删除评论（点赞会自动级联删除）
        cur.execute("DELETE FROM dish_reviews WHERE review_id = %s", (review_id,))
        
        # 更新菜品评分和评价数
        if dish_id:
            cur.execute("""
                UPDATE dishes
                SET avg_rating = COALESCE(
                        (SELECT AVG(rating) 
                         FROM dish_reviews dr
                         JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                         WHERE sd.dish_id = %s),
                        0
                    ),
                    review_count = (
                        SELECT COUNT(*) 
                        FROM dish_reviews dr
                        JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                        WHERE sd.dish_id = %s
                    )
                WHERE dish_id = %s
            """, (dish_id, dish_id, dish_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': '评论已删除'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close(); conn.close()

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form['username']
    current_password = request.form['current_password']
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT password_hash FROM anonymous_users WHERE user_id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not bcrypt.check_password_hash(user['password_hash'], current_password):
            flash('当前密码不正确', 'danger')
            return redirect(url_for('profile'))
        
        cursor.execute("UPDATE anonymous_users SET username = %s WHERE user_id = %s", 
                      (username, session['user_id']))
        
        if new_password:
            if len(new_password) < 6:
                flash('新密码至少需要6个字符', 'danger')
                return redirect(url_for('profile'))
            
            if new_password != confirm_password:
                flash('两次输入的新密码不一致', 'danger')
                return redirect(url_for('profile'))
            
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            cursor.execute("UPDATE anonymous_users SET password_hash = %s WHERE user_id = %s", 
                         (password_hash, session['user_id']))
        
        conn.commit()
        session['username'] = username
        flash('个人信息已更新', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:
            flash('用户名已被使用', 'danger')
        else:
            flash('更新失败: ' + str(err), 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('profile'))

@app.route('/api/rating', methods=['POST', 'OPTIONS'])
@login_required
def api_add_rating():
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401

    try:
        data = request.get_json()
        rating_type = data.get('type')
        target_id = data.get('id')
        rating = int(data.get('rating'))
        comment = data.get('comment', '').strip()

        if rating not in range(1, 6):
            return jsonify({'error': '无效评分'}), 400

        # 内容审核 - 如果有评论内容
        if comment:
            moderation_result = check_comment(comment)
            if not moderation_result['is_safe']:
                return jsonify({
                    'error': moderation_result['message'],
                    'violation_type': moderation_result['violation_type'],
                    'violation_words': moderation_result['violation_words']
                }), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        if rating_type == 'dish' or rating_type == 'stall_dish':
            # 获取 stall_id 和 dish_id
            if rating_type == 'dish':
                # 当type为dish时，target_id是dish_id
                cur.execute("""
                    SELECT sd.id AS stall_dish_id, sd.stall_id, sd.dish_id 
                    FROM stall_dishes sd
                    WHERE sd.dish_id = %s 
                    LIMIT 1
                """, (target_id,))
            else:  # rating_type == 'stall_dish'
                # 当type为stall_dish时，target_id是stall_dish_id
                cur.execute("""
                    SELECT sd.id AS stall_dish_id, sd.stall_id, sd.dish_id 
                    FROM stall_dishes sd
                    WHERE sd.id = %s 
                    LIMIT 1
                """, (target_id,))
                
            stall_data = cur.fetchone()
            if not stall_data:
                return jsonify({'error': '菜品不存在'}), 404
            stall_dish_id, stall_id, dish_id = stall_data
            
            # 插入评论（包含 stall_dish_id）
            cur.execute("""
                INSERT INTO dish_reviews
                (stall_dish_id, stall_id, user_id, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
            """, (stall_dish_id, stall_id, session['user_id'], rating, comment))
            
            # 更新菜品评分
            cur.execute("""
                UPDATE dishes
                SET avg_rating = COALESCE(
                        (SELECT AVG(rating) 
                         FROM dish_reviews dr
                         JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                         WHERE sd.dish_id = %s),
                        0
                    ),
                    review_count = (
                        SELECT COUNT(*) 
                        FROM dish_reviews dr
                        JOIN stall_dishes sd ON dr.stall_dish_id = sd.id
                        WHERE sd.dish_id = %s
                    )
                WHERE dish_id = %s
            """, (dish_id, dish_id, dish_id))
            
        elif rating_type == 'queue':
            # 排队评分保持不变
            cur.execute("""
                INSERT INTO stall_queues
                (stall_id, user_id, queue_rating)
                VALUES (%s, %s, %s)
            """, (target_id, session['user_id'], rating))
            
            cur.execute("""
                UPDATE canteen_stalls
                SET queue_rating = (SELECT AVG(queue_rating) FROM stall_queues WHERE stall_id = %s),
                    queue_rating_count = (SELECT COUNT(*) FROM stall_queues WHERE stall_id = %s)
                WHERE stall_id = %s
            """, (target_id, target_id, target_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/crowd', methods=['POST'])
@login_required
def api_add_crowd():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401

    data = request.get_json()
    canteen_id = data.get('canteen_id')
    level = int(data.get('level'))

    if level not in range(1, 6):
        return jsonify({'error': '无效拥挤度'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO crowd_feedback
            (canteen_id, user_id, crowd_level)
            VALUES (%s, %s, %s)
        """, (canteen_id, session['user_id'], level))
        
        cur.execute("""
            UPDATE canteens
            SET crowd_level = (SELECT AVG(crowd_level) FROM crowd_feedback WHERE canteen_id = %s)
            WHERE canteen_id = %s
        """, (canteen_id, canteen_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/queue_rating', methods=['POST'])
@login_required
def api_queue_time_rating():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401

    try:
        data = request.get_json()
        stall_id = data.get('stall_id')
        rating = data.get('rating')
        comment = data.get('comment', '')  # 添加评论字段

        if not stall_id or rating not in range(1, 6):
            return jsonify({'error': '无效参数'}), 400

        # 内容审核
        if comment and comment.strip():
            # 使用全局导入的check_comment函数
            moderation_result = check_comment(comment)
            if not moderation_result['is_safe']:
                return jsonify({
                    'success': False,
                    'error': moderation_result['message'],
                    'violation_type': moderation_result['violation_type'],
                    'violation_words': moderation_result['violation_words']
                }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO stall_queues (stall_id, user_id, queue_rating)
            VALUES (%s, %s, %s)
        """, (stall_id, session['user_id'], rating))

        cur.execute("""
            UPDATE canteen_stalls
            SET queue_rating = (SELECT AVG(queue_rating) FROM stall_queues WHERE stall_id = %s),
                queue_rating_count = (SELECT COUNT(*) FROM stall_queues WHERE stall_id = %s)
            WHERE stall_id = %s
        """, (stall_id, stall_id, stall_id))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_moderation', methods=['POST'])
def test_moderation():
    """测试内容审核的API"""
    try:
        data = request.get_json()
        comment = data.get('comment', '')
        
        if not comment:
            return jsonify({'error': '请输入评论内容'}), 400
            
        result = check_comment(comment)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorite', methods=['POST'])
@login_required
def api_favorite():
    if 'user_id' not in session or session.get('is_guest'):
        return jsonify({'error': '请先登录'}), 401

    data = request.get_json()
    stall_dish_id = data.get('stall_dish_id')
    
    try:
        stall_dish_id = int(stall_dish_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'stall_dish_id 必须是整数'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM user_favorites WHERE user_id=%s AND stall_dish_id=%s",
                    (session['user_id'], stall_dish_id))
        is_currently_favorite = bool(cur.fetchone())
        
        if is_currently_favorite:
            cur.execute("DELETE FROM user_favorites WHERE user_id=%s AND stall_dish_id=%s",
                        (session['user_id'], stall_dish_id))
            new_status = False
        else:
            cur.execute("INSERT INTO user_favorites (user_id, stall_dish_id) VALUES (%s,%s)",
                        (session['user_id'], stall_dish_id))
            new_status = True
        
        conn.commit()
        return jsonify({
            'success': True,
            'is_favorite': new_status
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close(); conn.close()

@app.route('/my-favorites')
@login_required
def my_favorites():
    return render_template('my_favorites.html')

@app.route('/api/my-favorites')
@login_required
def api_my_favorites():
    if 'user_id' not in session or session.get('is_guest'):
        return jsonify([]), 401

    q = request.args.get('q', '').strip()
    like = f"%{q}%"

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
        SELECT d.dish_id AS id, d.name, d.avg_rating AS rating,
               sd.actual_price AS price,
               CONCAT(c.name,' - ',COALESCE(cs.custom_name,st.name)) AS location
        FROM user_favorites uf
        JOIN stall_dishes sd ON uf.stall_dish_id = sd.id
        JOIN dishes d ON sd.dish_id = d.dish_id
        JOIN canteen_stalls cs ON cs.stall_id = sd.stall_id
        JOIN stall_types st ON st.type_id = cs.type_id
        JOIN canteens c ON c.canteen_id = cs.canteen_id
        WHERE uf.user_id = %s
          AND d.name LIKE %s
        ORDER BY uf.created_at DESC
    """
    cur.execute(sql, (session['user_id'], like))
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    q   = request.args.get('q', '').strip()
    typ = request.args.get('type', 'all')      # 食堂|canteen 窗口|stall 菜品|dish
    sort= request.args.get('sort', 'default')  # rating|price|name
    page= int(request.args.get('page', 1))
    size= 20

    if not q:
        return jsonify({'total':0,'items':[]})

    like = f"%{q}%"
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    # 检查是否为特殊关键词（优化：使用集合提高查找效率）
    canteen_keywords = {'食堂', 'canteen', '餐厅', '食堂餐厅'}
    stall_keywords = {'窗口', 'stall', '档口', '摊位'}
    dish_keywords = {'菜品', 'dish', '菜', '美食', 'food'}
    
    q_lower = q.lower()
    is_canteen_keyword = q_lower in canteen_keywords
    is_stall_keyword = q_lower in stall_keywords
    is_dish_keyword = q_lower in dish_keywords

    # 白名单验证，防止SQL注入
    valid_types = {'all', 'canteen', 'stall', 'dish'}
    valid_sorts = {'rating', 'price', 'name', 'default'}
    
    typ = typ if typ in valid_types else 'all'
    sort = sort if sort in valid_sorts else 'default'

    # 优化：根据类型参数直接查询对应表，避免复杂的UNION
    items = []
    total = 0
    offset = (page-1)*size
    
    if typ in ['all', 'canteen']:
        # 查询食堂
        canteen_where = "1=1" if is_canteen_keyword else "name LIKE %s"
        canteen_order = {
            'rating': 'crowd_level ASC',
            'name': 'name ASC',
            'default': 'name ASC'
        }[sort]
        
        if typ == 'all' or typ == 'canteen':
            canteen_sql = f"""
                SELECT canteen_id AS id, name, 'canteen' AS type,
                       address AS location, crowd_level AS rating, NULL AS price
                FROM canteens 
                WHERE {canteen_where}
                ORDER BY {canteen_order}
                LIMIT %s OFFSET %s
            """
            
            if is_canteen_keyword:
                cur.execute(canteen_sql, (size, offset))
            else:
                cur.execute(canteen_sql, (like, size, offset))
            
            canteen_items = cur.fetchall()
            items.extend(canteen_items)
            
            # 获取食堂总数
            cnt_sql = f"SELECT COUNT(*) AS c FROM canteens WHERE {canteen_where}"
            cur.execute(cnt_sql, [like] if not is_canteen_keyword else [])
            total += cur.fetchone()['c']

    if typ in ['all', 'stall']:
        # 查询窗口
        stall_where = "1=1" if is_stall_keyword else "(cs.custom_name LIKE %s OR st.name LIKE %s)"
        stall_order = {
            'rating': 'cs.queue_rating ASC',
            'name': 'COALESCE(cs.custom_name, st.name) ASC',
            'default': 'COALESCE(cs.custom_name, st.name) ASC'
        }[sort]
        
        if typ == 'all' or typ == 'stall':
            stall_sql = f"""
                SELECT cs.stall_id AS id,
                       COALESCE(cs.custom_name, st.name) AS name, 
                       'stall' AS type,
                       c.name AS location,
                       cs.queue_rating AS rating, NULL AS price
                FROM canteen_stalls cs
                JOIN stall_types st ON st.type_id=cs.type_id
                JOIN canteens c ON c.canteen_id=cs.canteen_id
                WHERE {stall_where}
                ORDER BY {stall_order}
                LIMIT %s OFFSET %s
            """
            
            if is_stall_keyword:
                cur.execute(stall_sql, (size, offset))
            else:
                cur.execute(stall_sql, (like, like, size, offset))
            
            stall_items = cur.fetchall()
            items.extend(stall_items)
            
            # 获取窗口总数
            cnt_sql = f"""
                SELECT COUNT(*) AS c FROM canteen_stalls cs
                JOIN stall_types st ON st.type_id=cs.type_id
                WHERE {stall_where}"""
            cur.execute(cnt_sql, [like, like] if not is_stall_keyword else [])
            total += cur.fetchone()['c']

    if typ in ['all', 'dish']:
        # 查询菜品
        dish_where = "" if is_dish_keyword else "AND d.name LIKE %s"
        dish_order = {
            'rating': 'd.avg_rating DESC',
            'price': 'sd.actual_price ASC',
            'name': 'd.name ASC',
            'default': 'd.name ASC'
        }[sort]
        
        if typ == 'all' or typ == 'dish':
            dish_sql = f"""
                SELECT sd.id AS id, d.name, 'dish' AS type,
                       CONCAT(c.name,' - ',COALESCE(cs.custom_name,st.name)) AS location,
                       d.avg_rating AS rating, sd.actual_price AS price
                FROM dishes d
                JOIN stall_dishes sd ON sd.dish_id=d.dish_id AND sd.is_available=1
                JOIN canteen_stalls cs ON cs.stall_id=sd.stall_id
                JOIN stall_types st ON st.type_id=cs.type_id
                JOIN canteens c ON c.canteen_id=cs.canteen_id
                WHERE 1=1 {dish_where}
                ORDER BY {dish_order}
                LIMIT %s OFFSET %s
            """
            
            if is_dish_keyword:
                cur.execute(dish_sql, (size, offset))
            else:
                cur.execute(dish_sql, (like, size, offset))
            
            dish_items = cur.fetchall()
            items.extend(dish_items)
            
            # 获取菜品总数
            cnt_sql = f"""
                SELECT COUNT(*) AS c FROM dishes d
                JOIN stall_dishes sd ON sd.dish_id=d.dish_id AND sd.is_available=1
                WHERE 1=1 {dish_where}"""
            cur.execute(cnt_sql, [like] if not is_dish_keyword else [])
            total += cur.fetchone()['c']

    # 应用最终排序和分页
    if typ != 'all':
        items = [item for item in items if item['type'] == typ]
    
    # 应用最终排序
    if sort == 'rating':
        items.sort(key=lambda x: float(x['rating']) if x['rating'] is not None else 0, reverse=True)
    elif sort == 'price':
        items.sort(key=lambda x: float(x['price']) if x['price'] is not None else float('inf'))
    elif sort == 'name':
        items.sort(key=lambda x: x['name'])
    
    # 应用分页
    start_idx = (page-1)*size
    end_idx = start_idx + size
    items = items[start_idx:end_idx]

    cur.close(); conn.close()
    return jsonify({'total': total, 'items': items})

# 管理员功能
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/canteens')
@admin_required
def admin_canteens():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM canteens")
    canteens = cur.fetchall()
    cur.close(); conn.close()
    return render_template('admin/canteens.html', canteens=canteens)

@app.route('/admin/add_canteen', methods=['POST'])
@admin_required
def admin_add_canteen():
    name = request.form['name']
    address = request.form['address']
    campus_id = request.form.get('campus_id', 1)
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO canteens (name, address, campus_id)
            VALUES (%s, %s, %s)
        """, (name, address, campus_id))
        conn.commit()
        flash('食堂添加成功', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'添加失败: {str(e)}', 'danger')
    finally:
        cur.close(); conn.close()
    
    return redirect(url_for('admin_canteens'))

def calculate_5min_averages():
    """每5分钟计算前两个5分钟窗口的平均值"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.now()
        
        # 计算当前时间对应的整5分钟边界
        current_5min = (now.minute // 5) * 5
        current_boundary = now.replace(minute=current_5min, second=0, microsecond=0)
        
        # 前两个5分钟窗口：window1和window2
        window2_end = current_boundary
        window2_start = window2_end - timedelta(minutes=5)
        window1_end = window2_start
        window1_start = window1_end - timedelta(minutes=5)
        
        # 1. 计算食堂拥挤度（双窗口平均）
        cursor.execute("""
            SELECT canteen_id, 
                   AVG(CASE 
                       WHEN created_at >= %s AND created_at < %s THEN crowd_level
                       WHEN created_at >= %s AND created_at < %s THEN crowd_level
                       ELSE NULL 
                   END) as avg_crowd,
                   COUNT(CASE 
                       WHEN created_at >= %s AND created_at < %s THEN 1
                       WHEN created_at >= %s AND created_at < %s THEN 1
                       ELSE NULL 
                   END) as data_count
            FROM crowd_feedback 
            WHERE created_at >= %s AND created_at < %s
            GROUP BY canteen_id
        """, (window1_start, window1_end, window2_start, window2_end,
              window1_start, window1_end, window2_start, window2_end,
              window1_start, window2_end))
        
        crowd_results = cursor.fetchall()
        crowd_count = 0
        
        for canteen_id, avg_crowd, data_count in crowd_results:
            if avg_crowd is not None and data_count > 0:
                cursor.execute("""
                    UPDATE canteens 
                    SET crowd_level = %s 
                    WHERE canteen_id = %s
                """, (round(float(avg_crowd), 1), canteen_id))
                crowd_count += 1
        
        # 2. 计算档口排队评级（双窗口平均）
        cursor.execute("""
            SELECT stall_id, 
                   AVG(CASE 
                       WHEN created_at >= %s AND created_at < %s THEN queue_rating
                       WHEN created_at >= %s AND created_at < %s THEN queue_rating
                       ELSE NULL 
                   END) as avg_rating,
                   COUNT(CASE 
                       WHEN created_at >= %s AND created_at < %s THEN 1
                       WHEN created_at >= %s AND created_at < %s THEN 1
                       ELSE NULL 
                   END) as data_count
            FROM stall_queues 
            WHERE created_at >= %s AND created_at < %s
            GROUP BY stall_id
        """, (window1_start, window1_end, window2_start, window2_end,
              window1_start, window1_end, window2_start, window2_end,
              window1_start, window2_end))
        
        queue_results = cursor.fetchall()
        queue_count = 0
        
        for stall_id, avg_rating, data_count in queue_results:
            if avg_rating is not None and data_count > 0:
                cursor.execute("""
                    UPDATE canteen_stalls 
                    SET queue_rating = %s,
                        queue_rating_count = (SELECT COUNT(*) FROM stall_queues WHERE stall_id = %s)
                    WHERE stall_id = %s
                """, (round(float(avg_rating), 1), stall_id, stall_id))
                queue_count += 1
        
        conn.commit()
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 5分钟任务完成：更新{crowd_count}食堂拥挤度，{queue_count}档口排队数据")
        
    except Exception as e:
        conn.rollback()
        print(f"5分钟计算错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

def schedule_10min_updates():
    """后台线程，每10分钟执行一次计算"""
    def run_scheduler():
        last_executed = None
        
        def get_next_5min_mark():
            """计算下一个整5分钟时间点"""
            now = datetime.now()
            next_min = ((now.minute // 5) * 5) + 5
            if next_min >= 60:
                next_min = 0
                next_hour = (now.hour + 1) % 24
            else:
                next_hour = now.hour
            return now.replace(hour=next_hour, minute=next_min, second=0, microsecond=0)
        
        # 初始等待到下一个整5分钟
        next_run = get_next_5min_mark()
        sleep_seconds = (next_run - datetime.now()).total_seconds()
        time.sleep(max(sleep_seconds, 0))
        
        while True:
            try:
                now = datetime.now()
                
                # 精确匹配整5分钟（00分00秒）
                if now.minute % 5 == 0 and now.second == 0:
                    if last_executed != now.replace(second=0, microsecond=0):
                        calculate_5min_averages()
                        last_executed = now.replace(second=0, microsecond=0)
                        
                        # 计算下一个整5分钟
                        next_run = get_next_5min_mark()
                        sleep_seconds = (next_run - datetime.now()).total_seconds()
                        time.sleep(max(sleep_seconds, 0))
                else:
                    # 等待到下一个整5分钟
                    next_run = get_next_5min_mark()
                    sleep_seconds = (next_run - datetime.now()).total_seconds()
                    time.sleep(max(sleep_seconds, 0))
                    
            except Exception as e:
                print(f"调度器错误: {e}")
                time.sleep(60)  # 出错后等待1分钟重试
    
    # 启动5分钟定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

# 启动自动更新服务
schedule_10min_updates()

# 问题反馈路由
@app.route('/bug-report', methods=['GET'])
def bug_report():
    """显示问题反馈页面"""
    return render_template('bug_report.html')

@app.route('/api/bug-report', methods=['POST'])
def submit_bug_report():
    """提交问题反馈"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'type', 'priority', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证字段长度
        if len(data['title']) > 200:
            return jsonify({'error': '标题过长，最多200字符'}), 400
        if len(data['description']) > 2000:
            return jsonify({'error': '描述过长，最多2000字符'}), 400
        
        # 验证类型和优先级（匹配前端中文值）
        valid_types = ['功能错误', '界面问题', '性能问题', '建议改进', '其他']
        valid_priorities = ['紧急', '高', '中', '低']
        
        if data['type'] not in valid_types:
            return jsonify({'error': '无效的问题类型'}), 400
        if data['priority'] not in valid_priorities:
            return jsonify({'error': '无效的优先级'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            user_id = session.get('user_id')
            username = session.get('username', '匿名用户')
            
            cursor.execute("""
                INSERT INTO bug_reports (user_id, username, title, type, priority, description, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                username,
                data['title'],
                data['type'],
                data['priority'],
                data['description'],
                '待处理',
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            report_id = cursor.lastrowid
            
            # 记录安全事件
            security_logger.log_security_event('bug_report_submitted', {
                'report_id': report_id,
                'user_id': user_id,
                'username': username,
                'type': data['type'],
                'priority': data['priority']
            })
            
            return jsonify({
                'success': True,
                'message': '问题反馈提交成功，我们会尽快处理',
                'report_id': report_id
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f'提交问题反馈时发生错误: {str(e)}')
        return jsonify({'error': '提交失败，请稍后重试'}), 500

@app.route('/admin/bug-reports')
@login_required
@admin_required
def admin_bug_reports():
    """管理员查看问题反馈列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取统计数据
        cursor.execute("SELECT COUNT(*) as total FROM bug_reports")
        total_reports = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as pending FROM bug_reports WHERE status = '待处理'")
        pending_count = cursor.fetchone()['pending']
        
        cursor.execute("SELECT COUNT(*) as resolved FROM bug_reports WHERE status = '已解决'")
        resolved_count = cursor.fetchone()['resolved']
        
        # 获取所有反馈
        cursor.execute("""
            SELECT * FROM bug_reports 
            ORDER BY created_at DESC
        """)
        reports = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/bug_reports.html',
                             reports=reports,
                             total_reports=total_reports,
                             pending_count=pending_count,
                             resolved_count=resolved_count)
                              
    except Exception as e:
        flash('获取数据失败', 'danger')
        return render_template('admin/bug_reports.html', reports=[],
                           total_reports=0, pending_count=0, resolved_count=0)

@app.route('/api/admin/bug-reports', methods=['GET'])
@login_required
@admin_required
def get_bug_reports():
    """获取问题反馈列表（管理员）"""
    try:
        # 获取筛选参数
        status = request.args.get('status', 'all')
        report_type = request.args.get('type', 'all')
        priority = request.args.get('priority', 'all')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 构建查询条件
        conditions = []
        params = []
        
        if status != 'all':
            conditions.append("status = %s")
            params.append(status)
        
        if report_type != 'all':
            conditions.append("type = %s")
            params.append(report_type)
        
        if priority != 'all':
            conditions.append("priority = %s")
            params.append(priority)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM bug_reports 
            {where_clause}
            ORDER BY 
                CASE priority 
                    WHEN '紧急' THEN 1 
                    WHEN '高' THEN 2 
                    WHEN '中' THEN 3 
                    WHEN '低' THEN 4 
                    ELSE 5 
                END,
                CASE status
                    WHEN '待处理' THEN 1
                    WHEN '处理中' THEN 2
                    WHEN '已解决' THEN 3
                    WHEN '已关闭' THEN 4
                    ELSE 5
                END,
                created_at DESC
        """
        
        cursor.execute(query, params)
        reports = cursor.fetchall()
        
        # 格式化数据
        for report in reports:
            report['created_at'] = report['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            report['updated_at'] = report['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({'reports': reports})
        
    except Exception as e:
        app.logger.error(f'获取问题反馈列表时发生错误: {str(e)}')
        return jsonify({'error': '获取数据失败'}), 500

@app.route('/api/admin/bug-reports/<int:report_id>/status', methods=['PUT'])
@login_required
@admin_required
def update_bug_report_status(report_id):
    """更新问题反馈状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': '缺少状态参数'}), 400
        
        valid_status = ['待处理', '处理中', '已解决', '已关闭']
        if new_status not in valid_status:
            return jsonify({'error': '无效的状态值'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE bug_reports 
                SET status = %s, updated_at = %s
                WHERE id = %s
            """, (new_status, datetime.now(), report_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': '问题反馈不存在'}), 404
            
            conn.commit()
            
            # 记录安全事件
            security_logger.log_security_event('bug_report_status_updated', {
                'report_id': report_id,
                'new_status': new_status,
                'admin_user': session.get('username')
            })
            
            return jsonify({
                'success': True,
                'message': '状态更新成功'
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f'更新问题反馈状态时发生错误: {str(e)}')
        return jsonify({'error': '更新失败'}), 500

@app.route('/api/admin/bug-reports/<int:report_id>/notes', methods=['POST'])
@login_required
@admin_required
def add_bug_report_notes(report_id):
    """添加问题反馈备注"""
    try:
        data = request.get_json()
        notes = data.get('notes', '').strip()
        
        if not notes:
            return jsonify({'error': '备注内容不能为空'}), 400
        
        if len(notes) > 1000:
            return jsonify({'error': '备注内容过长，最多1000字符'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 获取当前备注
            cursor.execute("SELECT notes FROM bug_reports WHERE id = %s", (report_id,))
            current_notes = cursor.fetchone()
            
            if not current_notes:
                return jsonify({'error': '问题反馈不存在'}), 404
            
            # 追加新备注
            new_notes = current_notes[0] + f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {session.get('username')}]\n{notes}" if current_notes[0] else f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {session.get('username')}]\n{notes}"
            
            cursor.execute("""
                UPDATE bug_reports 
                SET notes = %s, updated_at = %s
                WHERE id = %s
            """, (new_notes, datetime.now(), report_id))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '备注添加成功'
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f'添加问题反馈备注时发生错误: {str(e)}')
        return jsonify({'error': '添加备注失败'}), 500

if __name__ == '__main__':
    # 生产环境配置
    print("🍽️ 华科食堂推荐系统 - 生产模式")
    print("✅ 绑定域名: canteen.seasideray.cn")
    print("✅ 监听地址: 0.0.0.0:5000")
    print("✅ 公网IP: 114.132.230.241")
    print("⚠️  请确保DNS已配置: canteen.seasideray.cn -> 114.132.230.241")
    
    app.run(host='0.0.0.0', port=5000, debug=False)