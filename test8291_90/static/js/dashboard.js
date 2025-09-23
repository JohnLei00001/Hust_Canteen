// 全局变量
let currentRecommendationType = 'default';
let __currentRating = 0; // 仅用于新增弹窗，避免与原有 window.__currentRating 冲突

// 详情页历史记录管理
let detailHistory = [];
let isClosingByHistory = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  console.log('sessionUserId:', typeof sessionUserId === 'undefined' ? 'undefined' : sessionUserId);
  loadRecommendations();
  loadRankings();

  // 搜索框表单提交
  const searchForm = document.querySelector('.search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', function(e) {
      e.preventDefault();
      searchItems();
    });
  }

  // 关闭按钮事件
  const closeBtn = document.querySelector('.close-results');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeSearchResults);
  }

  // 统一关闭逻辑
  document.addEventListener('click', e => {
    if (e.target.matches('[data-close]')) {
      const modal = e.target.closest('.modal');
      if (modal) {
        if (modal.id === 'detail-modal') {
          closeDetailModal();
        } else {
          modal.classList.add('hidden');
        }
      }
    }
    if (e.target.id === 'search-overlay') {
      closeSearchResults();
    }
  });

  // 监听浏览器后退按钮
  window.addEventListener('popstate', function(e) {
    if (detailHistory.length > 0 && !isClosingByHistory) {
      e.preventDefault();
      closeDetailModal();
    }
  });
});

// 加载推荐内容
function loadRecommendations(type = 'all') {
  currentRecommendationType = type;
  const recommendationScroll = document.getElementById('recommendation-scroll');
  if (!recommendationScroll) return; // 如果不在主页，直接返回
  
  recommendationScroll.innerHTML = `
    <div style="width: 100%; padding: 40px 20px;">
      <div class="skeleton-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto;">
        <div class="skeleton-card">
          <div class="skeleton-image"></div>
          <div class="skeleton-content">
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
          </div>
        </div>
        <div class="skeleton-card">
          <div class="skeleton-image"></div>
          <div class="skeleton-content">
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
          </div>
        </div>
        <div class="skeleton-card">
          <div class="skeleton-image"></div>
          <div class="skeleton-content">
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  fetch(`/api/recommendations/${type}`)
    .then(response => response.json())
    .then(data => renderRecommendations(data))
    .catch(error => {
      console.error('Error loading recommendations:', error);
      recommendationScroll.innerHTML = '<div class="error">加载推荐失败</div>';
    });
}

// 加载榜单
function loadRankings() {
  const rankingTypes = ['popular', 'crowded', 'quick', 'easy-seat', 'join-fun'];
  
  rankingTypes.forEach(type => {
    const container = document.getElementById(`${type}-ranking`);
    if (!container) return; // 如果不在主页，直接返回
    
    // 为榜单添加骨架屏
    container.innerHTML = `
      <div class="loading-placeholder small">
        <div style="padding: 10px;">
          <div class="skeleton-line" style="margin-bottom: 12px; height: 20px;"></div>
          <div class="skeleton-line medium" style="margin-bottom: 12px; height: 20px;"></div>
          <div class="skeleton-line short" style="margin-bottom: 12px; height: 20px;"></div>
          <div class="skeleton-line" style="margin-bottom: 12px; height: 20px;"></div>
        </div>
      </div>
    `;
    
    const apiType = type === 'popular' ? 'top-rated' : 
                   type === 'crowded' ? 'most-popular' : 
                   type === 'quick' ? 'least-crowded' : 
                   type === 'easy-seat' ? 'easy-seat' : 'join-fun';
    
    fetch(`/api/rankings/${apiType}`)
      .then(response => response.json())
      .then(data => renderRanking(type, data))
      .catch(error => {
        console.error(`Error loading ${type} rankings:`, error);
        document.getElementById(`${type}-ranking`).innerHTML = '<div class="error">加载榜单失败</div>';
      });
  });
}

// 渲染榜单
function renderRanking(type, items) {
  const container = document.getElementById(`${type}-ranking`);
  container.innerHTML = '';
  
  items.forEach((item, index) => {
    const rankItem = document.createElement('div');
    rankItem.className = 'ranking-item';
    rankItem.onclick = () => showDetail(item.type, item.id);
    
    let displayValue = '';
    if (type === 'quick') {
      // 免排队榜：显示排队人数少的窗口
      displayValue = getPeopleIcons(item.value);
    } else if (type === 'easy-seat') {
      // 好找座：显示食堂拥挤度
      displayValue = getCrowdLevelText(item.value);
    } else if (type === 'popular') {
      // 人气榜：显示收藏人数用星星图标
      displayValue = `★ ${item.value}`;
    } else if (type === 'crowded') {
      // 拥挤榜：显示心形图标
      displayValue = `❤️ ${item.value}`;
    } else if (type === 'join-fun') {
      // 凑热闹：显示火焰图标
      displayValue = `🔥 ${item.value}`;
    } else {
      // 好评榜显示星级评分
      displayValue = `★ ${item.value}`;
    }
    
    rankItem.innerHTML = `
      <div class="ranking-header">
        <div class="ranking-rank">${index + 1}</div>
        <div class="ranking-name">${item.name}</div>
        <div class="ranking-rating">${displayValue}</div>
      </div>
      <div class="ranking-details">${item.location}</div>
    `;
    
    container.appendChild(rankItem);
  });
}

// 切换推荐类型
function showRecommendations(type) {
  document.querySelectorAll('.rec-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  document.querySelector(`.rec-tab-btn[onclick="showRecommendations('${type}')"]`).classList.add('active');
  
  loadRecommendations(type);
}

// 切换榜单标签
function showRanking(type) {
  document.querySelectorAll('.ranking-list').forEach(el => {
    el.classList.add('hidden');
  });
  
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  document.getElementById(`${type}-ranking`).classList.remove('hidden');
  document.querySelector(`.tab-btn[onclick="showRanking('${type}')"]`).classList.add('active');
}

// 搜索框功能
function searchItems() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) return;
  location.href = `/search?q=${encodeURIComponent(q)}`;
}

// 渲染搜索结果
function renderSearchResults(results) {
  const resultsContainer = document.getElementById('results-container');
  
  if (results.length === 0) {
    resultsContainer.innerHTML = '<div class="no-results">没有找到匹配的结果</div>';
    return;
  }
  
  resultsContainer.innerHTML = '';
  
  results.forEach(item => {
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item';
    resultItem.onclick = () => {
      showDetail(item.type, item.id);
      closeSearchResults();
    };
    
    const location = item.location || '';
    
    resultItem.innerHTML = `
      <div>
        <span class="result-type">${getTypeName(item.type)}</span>
        <strong>${item.name}</strong>
        <div class="result-details">${location}</div>
      </div>
      ${item.rating ? `<div class="result-rating">★ ${item.rating}</div>` : ''}
    `;
    
    resultsContainer.appendChild(resultItem);
  });
}

// 获取类型名称
function getTypeName(type) {
  const types = {
    'canteen': '食堂',
    'stall': '窗口',
    'dish': '菜品'
  };
  return types[type] || type;
}

// 关闭搜索结果
function closeSearchResults() {
  document.getElementById('search-results').classList.remove('show');
  document.getElementById('search-overlay').classList.remove('show');
}

// 刷新推荐
function refreshRecommendations() {
  loadRecommendations(currentRecommendationType);
}

// 显示详情模态框
function showDetail(type, id) {
    const modal = document.getElementById('detail-modal');
    const modalBody = document.getElementById('modal-body');
    
    // 添加到历史记录
    detailHistory.push({ type, id });
    
    // 添加历史记录状态（仅在第一次打开详情页时）
    if (detailHistory.length === 1) {
      history.pushState({ detailPage: true }, '');
    }
    
    modalBody.innerHTML = `
    <div class="detail-skeleton">
        <div class="detail-skeleton-header"></div>
        <div class="detail-skeleton-body">
            <div class="detail-skeleton-title"></div>
            <div class="detail-skeleton-text"></div>
            <div class="detail-skeleton-text medium"></div>
            <div class="detail-skeleton-text short"></div>
            <div class="detail-skeleton-text"></div>
            <div class="detail-skeleton-text medium"></div>
        </div>
    </div>
    `;
    
    modal.classList.remove('hidden');

    const apiUrl = type === 'stall-dish' ? `/api/stall-dish/${id}` : `/api/${type}/${id}`;
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) throw new Error('网络响应异常');
            return response.json();
        })
        .then(data => {
            if (!data || Object.keys(data).length === 0) {
                throw new Error('未获取到数据');
            }
            renderModalDetail(type, data);
        })
        .catch(error => {
            console.error('加载失败:', error);
            modalBody.innerHTML = `
                <div class="error">
                    <p>加载详情失败: ${error.message}</p>
                    <button onclick="showDetail('${type}', ${id})">重试</button>
                </div>
            `;
        });
}

// ================== renderRecommendations （推荐卡片） ==================
function renderRecommendations(items) {
  const recommendationScroll = document.getElementById('recommendation-scroll');
  recommendationScroll.innerHTML = '';

  items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'recommendation-card';
      card.onclick = () => showDetail(item.type, item.id);

      let description = '';
      let meta = '';
      let ratingDisplay = '';

      if (item.type === 'dish') {
        description = `${item.stall_name} | ${item.canteen_name}`;
        meta = `¥${item.price}`;
        ratingDisplay = `★ ${item.rating}`;
      } else if (item.type === 'stall') {
        description = `${item.canteen_name}`;
        meta = '查看窗口';
        // 窗口显示小人图标表示排队情况
        ratingDisplay = getPeopleIcons(item.rating);
      } else if (item.type === 'canteen') {
        description = `${item.address}`;
        meta = '查看食堂';
        // 食堂显示拥挤度文字描述
        ratingDisplay = getCrowdLevelText(item.rating); // 直接使用crowd_level数值
      }

      card.innerHTML = `
        <div class="recommendation-image" style="background-image: url('/static/images/${item.type}-default.jpg')"></div>
        <div class="recommendation-info" data-stall-dish-id="${item.stall_dish_id}">
          <div class="title-with-icon">
            <h3 class="recommendation-title">${item.name}</h3>
            ${item.type === 'dish' ? `
              <div class="favorite-icon ${item.is_favorite ? 'active' : ''} ${item.session && item.session.is_guest ? 'guest-disabled' : ''}"
                   onclick="${item.session && item.session.is_guest ? '' : `event.stopPropagation(); toggleFavorite(${item.stall_dish_id}, this)`}"
                   style="${item.session && item.session.is_guest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                   title="${item.session && item.session.is_guest ? '请先登录后再收藏' : '收藏/取消收藏'}">
                ${item.is_favorite ? '♥' : '♡'}
              </div>
            ` : ''}
          </div>
          <div class="recommendation-desc">${description}</div>
          <div class="recommendation-meta">
            <span class="recommendation-rating">${ratingDisplay}</span>
            <span>${meta}</span>
          </div>
        </div>
      `;

    recommendationScroll.appendChild(card);
  });
}

// ================== renderModalDetail （详情弹窗） ==================
function renderModalDetail(type, data) {
  const modalBody = document.getElementById('modal-body');
  let detailContent = '';

  const session = data.session || {};

  /* ---------- canteen ---------- */
  if (type === 'canteen') {
    detailContent = `
      <div class="detail-scroll-wrapper-right-pad">
        <div class="detail-header">
          <div class="detail-image" style="background-image: url('/static/images/canteen-default.jpg')"></div>
          <div>
            <h2 class="detail-title">${data.name}</h2>
            <div class="detail-subtitle">${data.campus_name}</div>
            <div class="detail-meta">
              <span class="detail-meta-item">${data.address}</span>
              <span class="detail-meta-item">拥挤程度: ${getCrowdLevelText(data.crowd_level)}</span>
            </div>
            <button class="btn feedback-btn ${sessionIsGuest ? 'guest-disabled' : ''}"
                    onclick="${sessionIsGuest ? '' : `showCrowdFeedback(${data.canteen_id})`}"
                    style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                    title="${sessionIsGuest ? '请先登录后再反馈' : '反馈拥挤程度'}">
              ${sessionIsGuest ? '登录后反馈' : '反馈拥挤程度'}
            </button>
          </div>
        </div>

        <div class="detail-section">
          <h3 class="detail-section-title">窗口列表</h3>
          <div class="stall-list">
            ${data.stalls.map(stall => `
              <div class="stall-item" onclick="showDetail('stall', ${stall.id})">
                <div>${stall.name} (${stall.type})</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>`;
  }

  /* ---------- stall ---------- */
  else if (type === 'stall') {
    const queueRating = Math.round(Number(data.queue_rating)) || 0;
    const queueText = getQueueRatingText(data.queue_rating);
    
    detailContent = `
      <div class="detail-scroll-wrapper-right-pad">
        <div class="detail-header">
          <div class="detail-image" style="background-image: url('/static/images/stall-default.jpg')"></div>
          <div>
            <h2 class="detail-title">${data.name}</h2>
            <div class="detail-subtitle">${data.canteen} | ${data.type}</div>
            <div class="detail-rating">
              <span class="detail-stars">${'★'.repeat(queueRating)}${'☆'.repeat(5 - queueRating)}</span>
              <span class="detail-review-count">${queueText} (${data.queue_rating_count || 0}条评价)</span>
            </div>
            <button class="btn feedback-btn ${sessionIsGuest ? 'guest-disabled' : ''}"
                    onclick="${sessionIsGuest ? '' : `showQueueRatingModal(${data.id}, '${data.name}')`}"
                    style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                    title="${sessionIsGuest ? '请先登录后再评价' : '评价排队时间'}">
              ${sessionIsGuest ? '登录后评价' : '评价排队时间'}
            </button>
          </div>
        </div>

        <div class="detail-section">
          <h3 class="detail-section-title">菜品列表</h3>
          <div class="dish-list">
            ${data.dishes.map(dish => `
              <div class="dish-item" onclick="showDetail('dish', ${dish.id})">
                <div>
                  <div class="dish-name">${dish.name}</div>
                  <div class="dish-price">¥${dish.price}</div>
                </div>
                <div>★ ${dish.rating || '暂无评分'}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>`;
  }

  /* ---------- stall-dish ---------- */
  else if (type === 'stall-dish') {
    const rating = Math.round(Number(data.avg_rating)) || 0;
    const stallDishId = data.stall_dish_id;
    
    detailContent = `
      <div class="detail-scroll-wrapper-right-pad" id="detail-body-${data.dish_id}">
        <div class="detail-header">
          <div class="detail-image" style="background-image: url('/static/images/dish-default.jpg')"></div>
          <div>
            <div class="title-with-icon">
              <h2 class="detail-title">${data.name}</h2>
              <div class="favorite-icon ${data.is_favorite ? 'active' : ''} ${sessionIsGuest ? 'guest-disabled' : ''}"
                   data-sd-id="${stallDishId}"
                   onclick="${sessionIsGuest ? '' : `toggleFavorite(${stallDishId}, this)`}"
                   style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                   title="${sessionIsGuest ? '请先登录后再收藏' : '收藏/取消收藏'}">
                ${data.is_favorite ? '♥' : '♡'}
              </div>
            </div>
            <div class="detail-subtitle">${data.description || ''}</div>
            <div class="detail-rating">
              <span class="detail-stars">${'★'.repeat(rating)}${'☆'.repeat(5 - rating)}</span>
              <span class="detail-review-count">${data.review_count || 0}条评价</span>
            </div>
            <button class="btn feedback-btn ${sessionIsGuest ? 'guest-disabled' : ''}"
                    onclick="${sessionIsGuest ? '' : `showRatingModal('dish', ${data.dish_id}, ${stallDishId})`}"
                    style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                    title="${sessionIsGuest ? '请先登录后再评价' : '评价菜品'}">
              ${sessionIsGuest ? '登录后评价' : '评价菜品'}
            </button>
          </div>
        </div>

        <div class="detail-section">
          <h3 class="detail-section-title">供应地点</h3>
          <div class="location-list">
            ${data.availability.map(loc => `
              <div class="location-item" onclick="showDetail('stall', ${loc.stall_id})">
                <div>${loc.canteen} - ${loc.stall}</div>
                <div>${loc.is_available ? `¥${loc.price}` : '暂不供应'}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="detail-section">
          <div style="display:flex; justify-content:space-between; align-items:center">
            <h3 class="detail-section-title">评价（${data.review_count || 0}）</h3>
            <span class="btn-view-all" onclick="showAllReviews(${data.dish_id})"><< 查看全部</span>
          </div>
          <div class="review-list">
            ${(data.reviews || []).slice(0, 3).map(r => `
              <div class="review-item">
                <div class="review-header">
                  <span class="review-user">${r.user}</span>
                  <span class="review-rating">★ ${r.rating}</span>
                  <span class="review-date">${new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                <div class="review-content">${r.comment || '暂无评论'}</div>
              </div>
            `).join('')}
          </div>
        </div>

        ${!sessionIsGuest ? `
          <div class="detail-section">
            <h3 class="detail-section-title">发表评价</h3>
            <form class="review-form" onsubmit="submitReview(event)">
              <input type="hidden" name="stall_dish_id" value="${stallDishId}">
              <div class="form-group">
                <label>评分</label>
                <div class="star-rating">
                  ${[1, 2, 3, 4, 5].map(i => `<span onclick="setRating(${i})">☆</span>`).join('')}
                </div>
              </div>
              <div class="form-group" style="margin-top:16px;">
                <label>评论</label>
                <textarea name="comment"
                          placeholder="分享你的用餐体验..."
                          style="width:100%;min-height:100px;font-size:16px;padding:12px;border:2px solid var(--accent-color);border-radius:8px;resize:vertical;"></textarea>
              </div>
              <button type="submit" class="btn">提交评价</button>
            </form>
          </div>` : `
          <div class="detail-section">
            <h3 class="detail-section-title">发表评价</h3>
            <div class="guest-restriction" style="background:linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);padding:24px;border-radius:12px;text-align:center;border:1px solid #dee2e6;">
              <h4 style="color:var(--accent-color);margin:0 0 12px 0;font-weight:600;">分享你的美食体验</h4>
              <p style="color:#6c757d;margin:0 0 20px 0;font-size:15px;line-height:1.5;">
                登录后发表评价，帮助更多同学发现美味
              </p>
              <div style="display:flex;gap:12px;justify-content:center;">
                <a href="/login" class="btn" style="min-width:100px;padding:10px 20px;font-size:14px;text-decoration:none;">登录</a>
                <a href="/register" class="btn" style="background:transparent;color:var(--accent-color);border:1px solid var(--accent-color);min-width:100px;padding:10px 20px;font-size:14px;text-decoration:none;">注册</a>
              </div>
            </div>
          </div>`}
      </div>`;
  }

  /* ---------- dish ---------- */
  else if (type === 'dish') {
    const rating = Math.round(Number(data.avg_rating)) || 0;
    const stallDishId = data.availability?.[0]?.stall_dish_id
      ? Number(data.availability[0].stall_dish_id)
      : null;

    detailContent = `
      <div class="detail-scroll-wrapper-right-pad" id="detail-body-${data.dish_id}">
        <div class="detail-header">
          <div class="detail-image" style="background-image: url('/static/images/dish-default.jpg')"></div>
          <div>
            <div class="title-with-icon">
              <h2 class="detail-title">${data.name}</h2>
              ${stallDishId ? `
                <div class="favorite-icon ${data.is_favorite ? 'active' : ''} ${sessionIsGuest ? 'guest-disabled' : ''}"
                   data-sd-id="${stallDishId}"
                   onclick="${sessionIsGuest ? '' : `toggleFavorite(${stallDishId}, this)`}"
                   style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                   title="${sessionIsGuest ? '请先登录后再收藏' : '收藏/取消收藏'}">
                ${data.is_favorite ? '♥' : '♡'}
              </div>` : ''}
            </div>
            <div class="detail-subtitle">${data.description || ''}</div>
            <div class="detail-rating">
              <span class="detail-stars">${'★'.repeat(rating)}${'☆'.repeat(5 - rating)}</span>
              <span class="detail-review-count">${data.review_count || 0}条评价</span>
            </div>
            <button class="btn feedback-btn ${sessionIsGuest ? 'guest-disabled' : ''}"
                    onclick="${sessionIsGuest ? '' : `showRatingModal('dish', ${data.dish_id}, ${stallDishId || data.dish_id})`}"
                    style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                    title="${sessionIsGuest ? '请先登录后再评价' : '评价菜品'}">
              ${sessionIsGuest ? '登录后评价' : '评价菜品'}
            </button>
          </div>
        </div>

        <div class="detail-section">
          <h3 class="detail-section-title">供应地点</h3>
          <div class="location-list">
            ${data.availability.map(loc => `
              <div class="location-item" onclick="showDetail('stall', ${loc.stall_id})">
                <div>${loc.canteen} - ${loc.stall}</div>
                <div>${loc.is_available ? `¥${loc.price}` : '暂不供应'}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="detail-section">
          <div style="display:flex; justify-content:space-between; align-items:center">
            <h3 class="detail-section-title">评价（${data.review_count || 0}）</h3>
            <span class="btn-view-all" onclick="showAllReviews(${data.dish_id})"><< 查看全部</span>
          </div>
          <div class="review-list">
            ${(data.reviews || []).slice(0, 3).map(r => `
              <div class="review-item">
                <div class="review-header">
                  <span class="review-user">${r.user}</span>
                  <span class="review-rating">★ ${r.rating}</span>
                  <span class="review-date">${new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                <div class="review-content">${r.comment || '暂无评论'}</div>
              </div>
            `).join('')}
          </div>
        </div>

        ${data.session && data.session.user_id && !data.session.is_guest && stallDishId ? `
          <div class="detail-section">
            <h3 class="detail-section-title">发表评价</h3>
            <form class="review-form" onsubmit="submitReview(event)">
              <input type="hidden" name="stall_dish_id" value="${stallDishId}">
              <div class="form-group">
                <label>评分</label>
                <div class="star-rating">
                  ${[1, 2, 3, 4, 5].map(i => `<span onclick="setRating(${i})">☆</span>`).join('')}
                </div>
              </div>
              <div class="form-group" style="margin-top:16px;">
                <label>评论</label>
                <textarea name="comment"
                          placeholder="分享你的用餐体验..."
                          style="width:100%;min-height:100px;font-size:16px;padding:12px;border:2px solid var(--accent-color);border-radius:8px;resize:vertical;"></textarea>
              </div>
              <button type="submit" class="btn">提交评价</button>
            </form>
          </div>` : `
          <div class="detail-section">
            <h3 class="detail-section-title">发表评价</h3>
            <div class="guest-restriction" style="background:linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);padding:24px;border-radius:12px;text-align:center;border:1px solid #dee2e6;">
              <h4 style="color:var(--accent-color);margin:0 0 12px 0;font-weight:600;">分享你的美食体验</h4>
              <p style="color:#6c757d;margin:0 0 20px 0;font-size:15px;line-height:1.5;">
                登录后发表评价，帮助更多同学发现美味
              </p>
              <div style="display:flex;gap:12px;justify-content:center;">
                <a href="/login" class="btn" style="min-width:100px;padding:10px 20px;font-size:14px;text-decoration:none;">登录</a>
                <a href="/register" class="btn" style="background:transparent;color:var(--accent-color);border:1px solid var(--accent-color);min-width:100px;padding:10px 20px;font-size:14px;text-decoration:none;">注册</a>
              </div>
            </div>
          </div>`}
      </div>`;
  }

  // ============== 关键：滚动容器 ==============
  modalBody.innerHTML = `
    <div>
      <div class="detail-scroll-wrapper-right-pad" style="max-height:80vh; overflow-y:auto;" id="detail-body-${data.dish_id}">
        ${detailContent}
      </div>
      
      <!-- 全部评论视图 -->
      <div class="review-body hidden" id="review-body-${data.dish_id}">
        <div class="review-back" onclick="hideAllReviews(${data.dish_id})">← 返回详情</div>
        <div class="review-list" id="all-reviews-${data.dish_id}"></div>
      </div>
    </div>`;

  window.__currentRating = 0;
}

// 提交评价
function submitReview(e) {
  e.preventDefault();
  const form = e.target;
  // 从隐藏字段直接读，并确保是数字
  const stallDishId = Number(form.stall_dish_id.value);

  if (!stallDishId || isNaN(stallDishId)) {
    alert('无效的菜品ID');
    return;
  }

  const payload = {
    stall_dish_id: stallDishId,
    rating: window.__currentRating || 3,
    comment: form.comment.value.trim()
  };

  fetch('/api/review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(r => r.json())
    .then(d => {
      if (d.success) {
        alert('评价已提交！');
        closeModal();
      } else {
        alert(d.error || '提交失败');
      }
    })
    .catch(err => {
      console.error('提交评价失败:', err);
      alert('提交评价失败');
    });
}

// 设置评分
function setRating(rating) {
  window.__currentRating = rating;
  const stars = document.querySelectorAll('.star-rating span');
  stars.forEach((star, index) => {
    star.textContent = index < rating ? '★' : '☆';
  });
}

// 显示评分弹窗
function showRatingModal(type, id, stallDishId) {
  // 如果是dish类型，但没有提供stallDishId，则需要查找当前激活的stall_dish_id
  if (type === 'dish' && !stallDishId) {
    const currentDishModal = document.querySelector('#detail-modal .favorite-icon[data-sd-id]');
    stallDishId = currentDishModal ? Number(currentDishModal.dataset.sdId) : id;
  }

  const modal = document.getElementById('rating-modal');
  const modalBody = document.getElementById('rating-modal-body');

  modalBody.innerHTML = `
    <h3>评价菜品</h3>
    <div class="star-rating">
      ${[1, 2, 3, 4, 5].map(i => `<span onclick="setTempRating(${i})">☆</span>`).join('')}
    </div>
    <div class="form-group" style="margin: 20px 0;">
      <label style="display: block; margin-bottom: 8px; font-weight: 600; color: var(--accent-color);">评论</label>
      <textarea id="review-comment" 
                placeholder="分享你的用餐体验..."
                style="width: 100%; min-height: 100px; font-size: 16px; padding: 12px; border: 2px solid var(--accent-color); border-radius: 8px; resize: vertical; font-family: inherit; box-sizing: border-box;"></textarea>
    </div>
    <button class="btn" onclick="submitRating('${type}', ${id}, ${stallDishId})" style="width: 100%; padding: 14px; font-size: 17px; border-radius: 10px;">提交评价</button>
  `;

  __currentRating = 0;
  modal.classList.remove('hidden');
}

function setTempRating(rating) {
  __currentRating = rating;
  document.querySelectorAll('#rating-modal .star-rating span').forEach((star, index) => {
    star.textContent = index < rating ? '★' : '☆';
  });
}

function submitRating(type, id, stallDishId) {
  if (__currentRating === 0) {
    alert('请先选择评分');
    return;
  }

  const comment = document.getElementById('review-comment').value;

  // 如果是菜品评价，使用stallDishId
  if (type === 'dish') {
    fetch('/api/rating', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'stall_dish',
        id: stallDishId,
        rating: __currentRating,
        comment: comment
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('评价已提交！');
        closeModal('rating-modal');
        const modalBody = document.getElementById('modal-body');
        if (modalBody) {
          showDetail('dish', id);
        }
      } else {
        // 内容审核失败的详细反馈
        if (data.violation_type) {
          const violationMessages = {
            'insult': '评论包含不文明用语，请保持友善交流',
            'political': '请专注于食堂评价，避免政治话题',
            'advertisement': '请勿发布广告或联系方式',
            'pornography': '请保持评论内容健康合适'
          };
          
          const message = violationMessages[data.violation_type] || data.error;
          
          // 创建更友好的提示框
          const alertDiv = document.createElement('div');
          alertDiv.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000; max-width: 400px; text-align: center; border: 2px solid #ff6b6b;
          `;
          alertDiv.innerHTML = `
            <h4 style="color: #ff6b6b; margin-bottom: 10px;">⚠️ 评论审核提醒</h4>
            <p style="margin-bottom: 15px; color: #333;">${message}</p>
            <button onclick="this.parentElement.remove()" style="padding: 8px 16px; background: #ff6b6b; color: white; border: none; border-radius: 5px; cursor: pointer;">知道了</button>
          `;
          document.body.appendChild(alertDiv);
          
          // 3秒后自动消失
          setTimeout(() => {
            if (alertDiv.parentElement) alertDiv.remove();
          }, 3000);
        } else {
          alert(data.error || '提交失败');
        }
      }
    })
    .catch(error => {
      console.error('提交评价失败:', error);
      alert('提交评价失败');
    });
  } else {
    // 对于其他类型的评价，保持原有逻辑
    fetch('/api/rating', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: type,
        id: id,
        rating: __currentRating,
        comment: comment
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('评价已提交！');
        closeModal('rating-modal');
        const modalBody = document.getElementById('modal-body');
        if (modalBody) {
          showDetail(type, id);
        }
      } else {
        // 内容审核失败的详细反馈
        if (data.violation_type) {
          const violationMessages = {
            'insult': '评论包含不文明用语，请保持友善交流',
            'political': '请专注于食堂评价，避免政治话题',
            'advertisement': '请勿发布广告或联系方式',
            'pornography': '请保持评论内容健康合适'
          };
          
          const message = violationMessages[data.violation_type] || data.error;
          
          // 创建更友好的提示框
          const alertDiv = document.createElement('div');
          alertDiv.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000; max-width: 400px; text-align: center; border: 2px solid #ff6b6b;
          `;
          alertDiv.innerHTML = `
            <h4 style="color: #ff6b6b; margin-bottom: 10px;">⚠️ 评论审核提醒</h4>
            <p style="margin-bottom: 15px; color: #333;">${message}</p>
            <button onclick="this.parentElement.remove()" style="padding: 8px 16px; background: #ff6b6b; color: white; border: none; border-radius: 5px; cursor: pointer;">知道了</button>
          `;
          document.body.appendChild(alertDiv);
          
          // 3秒后自动消失
          setTimeout(() => {
            if (alertDiv.parentElement) alertDiv.remove();
          }, 3000);
        } else {
          alert(data.error || '提交失败');
        }
      }
    })
    .catch(error => {
      console.error('提交评价失败:', error);
      alert('提交评价失败');
    });
  }
}

// 显示拥挤度反馈
function showCrowdFeedback(canteenId) {
  const modal = document.getElementById('crowd-modal');
  const modalBody = document.getElementById('crowd-modal-body');

  modalBody.innerHTML = `
    <h3>当前食堂拥挤程度</h3>
    <div class="crowd-options">
      <button class="crowd-option" onclick="submitCrowdFeedback(${canteenId}, 1)" style="padding: 14px; font-size: 16px; border-radius: 10px; border: 2px solid var(--accent-color); background: white; cursor: pointer; transition: all 0.3s;">非常空闲</button>
      <button class="crowd-option" onclick="submitCrowdFeedback(${canteenId}, 2)" style="padding: 14px; font-size: 16px; border-radius: 10px; border: 2px solid var(--accent-color); background: white; cursor: pointer; transition: all 0.3s;">较空闲</button>
      <button class="crowd-option" onclick="submitCrowdFeedback(${canteenId}, 3)" style="padding: 14px; font-size: 16px; border-radius: 10px; border: 2px solid var(--accent-color); background: white; cursor: pointer; transition: all 0.3s;">适中</button>
      <button class="crowd-option" onclick="submitCrowdFeedback(${canteenId}, 4)" style="padding: 14px; font-size: 16px; border-radius: 10px; border: 2px solid var(--accent-color); background: white; cursor: pointer; transition: all 0.3s;">较密集</button>
      <button class="crowd-option" onclick="submitCrowdFeedback(${canteenId}, 5)" style="padding: 14px; font-size: 16px; border-radius: 10px; border: 2px solid var(--accent-color); background: white; cursor: pointer; transition: all 0.3s;">非常密集</button>
    </div>
  `;

  modal.classList.remove('hidden');
}

function submitCrowdFeedback(canteenId, level) {
  fetch('/api/crowd', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      canteen_id: canteenId,
      level: level
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('感谢您的反馈！');
      closeModal('crowd-modal');
      const modalBody = document.getElementById('modal-body');
      if (modalBody) {
        showDetail('canteen', canteenId);
      }
    } else {
      alert(data.error || '提交失败');
    }
  })
  .catch(error => {
    console.error('提交反馈失败:', error);
    alert('提交反馈失败');
  });
}

function toggleFavorite(stallDishId, iconEl) {
  // 确保是数字
  stallDishId = Number(stallDishId);

  // 检查是否为访客模式
  if (sessionIsGuest) {
    alert('请先登录后再收藏');
    return;
  }

  iconEl.disabled = true;

  fetch('/api/favorite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stall_dish_id: stallDishId })
  })
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        alert(data.error || '操作失败');
        return;
      }

      // 更新当前图标
      if (data.is_favorite) {
        iconEl.textContent = '♥';
        iconEl.classList.add('active');
      } else {
        iconEl.textContent = '♡';
        iconEl.classList.remove('active');
      }

      // 同步所有相同 stall_dish_id 图标
      syncFavoriteIcons(stallDishId, data.is_favorite);
    })
    .catch(err => {
      console.error('请求失败:', err);
      alert('操作失败，请重试');
    })
    .finally(() => {
      iconEl.disabled = false;
    });
}

// 同步更新所有相同菜品的收藏图标
function syncFavoriteIcons(stallDishId, isFavorite) {
    document.querySelectorAll(`[data-stall-dish-id="${stallDishId}"] .favorite-icon`).forEach(icon => {
        icon.textContent = isFavorite ? '♥' : '♡';
        isFavorite ? icon.classList.add('active') : icon.classList.remove('active');
    });
}

// 显示排队评分模态框
function showQueueRatingModal(stallId, stallName) {
  const modalBody = document.getElementById('rating-modal-body');
  modalBody.innerHTML = `
    <div class="rating-modal-content">
      <h3>评价 ${stallName} 的排队时间</h3>
      <p style="margin: 15px 0; font-size: 16px; color: var(--text-color);">请选择您对排队时间的满意程度：</p>
      <div class="queue-rating-people" style="display: flex; justify-content: center; gap: 15px; margin: 25px 0;">
        <span class="person-rating" data-rating="1" style="font-size: 32px; cursor: pointer; transition: all 0.3s; filter: grayscale(100%);">👤</span>
        <span class="person-rating" data-rating="2" style="font-size: 32px; cursor: pointer; transition: all 0.3s; filter: grayscale(100%);">👤</span>
        <span class="person-rating" data-rating="3" style="font-size: 32px; cursor: pointer; transition: all 0.3s; filter: grayscale(100%);">👤</span>
        <span class="person-rating" data-rating="4" style="font-size: 32px; cursor: pointer; transition: all 0.3s; filter: grayscale(100%);">👤</span>
        <span class="person-rating" data-rating="5" style="font-size: 32px; cursor: pointer; transition: all 0.3s; filter: grayscale(100%);">👤</span>
      </div>
      <div class="queue-rating-text" style="text-align: center; margin: 15px 0;">
        <span id="rating-text" style="font-size: 16px; font-weight: 600; color: var(--accent-color);">请选择评分</span>
      </div>
      <button id="submit-queue-rating" class="btn" disabled style="width: 100%; padding: 14px; font-size: 17px; border-radius: 10px;">提交评价</button>
    </div>
  `;

  // 显示模态框
  document.getElementById('rating-modal').classList.remove('hidden');

  // 小人图标评分交互
  let selectedRating = 0;
  const people = modalBody.querySelectorAll('.person-rating');
  const ratingText = modalBody.querySelector('#rating-text');
  const submitBtn = modalBody.querySelector('#submit-queue-rating');

  const ratingTexts = {
    1: '基本不排队 - 非常满意',
    2: '排队较短 - 满意',
    3: '排队适中 - 可以接受',
    4: '排队较长 - 一般',
    5: '排队很长 - 不满意'
  };

  // 更新小人图标显示
  function updatePeopleDisplay(rating) {
    people.forEach((person, index) => {
      if (index < rating) {
        person.className = 'person-rating active';
        person.innerHTML = '<span class="person-icon"></span>';
      } else {
        person.className = 'person-rating';
        person.innerHTML = '<span class="person-icon empty"></span>';
      }
    });
  }

  people.forEach(person => {
    person.addEventListener('click', () => {
      selectedRating = parseInt(person.dataset.rating);
      updatePeopleDisplay(selectedRating);
      ratingText.textContent = ratingTexts[selectedRating];
      submitBtn.disabled = false;
    });

    person.addEventListener('mouseenter', () => {
      const hoverRating = parseInt(person.dataset.rating);
      updatePeopleDisplay(hoverRating);
      ratingText.textContent = ratingTexts[hoverRating];
    });

    person.addEventListener('mouseleave', () => {
      updatePeopleDisplay(selectedRating);
      ratingText.textContent = selectedRating ? ratingTexts[selectedRating] : '请选择评分';
    });
  });

  // 初始化显示
  updatePeopleDisplay(0);

  // 提交评价
  submitBtn.addEventListener('click', () => {
    if (selectedRating === 0) return;

    fetch('/api/queue_rating', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        stall_id: stallId,
        rating: selectedRating
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('排队时间评价已提交！');
        document.getElementById('rating-modal').classList.add('hidden');
        
        // 刷新当前窗口详情
        showDetail('stall', stallId);
      } else {
        alert(data.error || '提交失败，请重试');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('提交失败，请重试');
    });
  });
}

// 显示全部评论
function showAllReviews(dishId) {
    const detailBody = document.getElementById(`detail-body-${dishId}`);
    const reviewBody = document.getElementById(`review-body-${dishId}`);
    
    const allReviewsContainer = document.getElementById(`all-reviews-${dishId}`);
    
    if (!detailBody || !reviewBody || !allReviewsContainer) {
        console.error('元素未找到:', { detailBody, reviewBody, allReviewsContainer });
        return;
    }
    
    // 显示加载状态
    allReviewsContainer.innerHTML = `
        <div style="text-align: center; padding: 30px;">
            <div class="loading-spinner"></div>
            <div>加载评论中...</div>
        </div>
    `;
    
    // 切换视图
    detailBody.classList.add('hidden');
    reviewBody.classList.remove('hidden');
    
    // 获取评论数据
    fetch(`/api/dish/${dishId}/reviews`)
        .then(response => {
            if (!response.ok) throw new Error('网络响应异常');
            return response.json();
        })
        .then(data => {
            const reviews = data.reviews || [];
            
            if (reviews.length > 0) {
                allReviewsContainer.innerHTML = reviews.map(r => {
                    const isOwner = String(r.user_id) === String(sessionUserId);
                    return `
                    <div class="review-item" data-review-id="${r.review_id}">
                        <div class="review-header">
                            <span class="review-user">${r.user}</span>
                            <span class="review-date">${new Date(r.created_at).toLocaleDateString()}</span>
                            <div class="review-actions">
                                <button class="like-btn ${r.is_liked_by_user ? 'liked' : ''} ${sessionIsGuest ? 'guest-disabled' : ''}" 
                                        onclick="${sessionIsGuest ? '' : `toggleLike(${r.review_id}, this)`}" 
                                        style="${sessionIsGuest ? 'opacity:0.5;cursor:not-allowed;' : ''}"
                                        title="${sessionIsGuest ? '请先登录后再点赞' : (r.is_liked_by_user ? '取消点赞' : '点赞')}">
                                    <svg class="like-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                                    </svg>
                                    <span class="like-count">${r.like_count || 0}</span>
                                </button>
                                ${isOwner ? 
                                    `<button class="delete-btn" onclick="deleteReview(${r.review_id}, this)" title="删除评论">
                                        <svg class="delete-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <polyline points="3 6 5 6 21 6"></polyline>
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                            <line x1="10" y1="11" x2="10" y2="17"></line>
                                            <line x1="14" y1="11" x2="14" y2="17"></line>
                                        </svg>
                                    </button>` 
                                    : ''}
                            </div>
                        </div>
                        <div class="review-content-row">
                            <div class="review-content">${r.comment || '暂无评论'}</div>
                            <span class="review-rating-inline">★ ${r.rating}</span>
                        </div>
                    </div>
                    `;
                }).join('');
            } else {
                allReviewsContainer.innerHTML = '<div class="no-results">暂无更多评论</div>';
            }
        })
        .catch(error => {
            console.error('加载评论失败:', error);
            allReviewsContainer.innerHTML = `
                <div class="error">
                    <p>加载失败: ${error.message}</p>
                    <button onclick="showAllReviews(${dishId})">重试</button>
                </div>
            `;
        });
}

// 点赞/取消点赞功能
function toggleLike(reviewId, button) {
    if (!sessionUserId || sessionIsGuest) {
        alert('请先登录后再点赞');
        return;
    }

    fetch(`/api/review/${reviewId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const likeCount = button.querySelector('.like-count');
            likeCount.textContent = data.like_count;
            
            if (data.action === 'liked') {
                button.classList.add('liked');
                button.title = '取消点赞';
            } else {
                button.classList.remove('liked');
                button.title = '点赞';
            }
        } else {
            alert(data.error || '操作失败');
        }
    })
    .catch(error => {
        console.error('点赞失败:', error);
        alert('操作失败，请重试');
    });
}

// 删除评论功能
function deleteReview(reviewId, button) {
    if (!confirm('确定要删除这条评论吗？')) {
        return;
    }

    console.log('正在删除评论ID:', reviewId, '用户ID:', sessionUserId);

    fetch(`/api/review/${reviewId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('删除API响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('删除API响应数据:', data);
        if (data.success) {
            const reviewItem = button.closest('.review-item');
            reviewItem.style.transition = 'opacity 0.3s ease';
            reviewItem.style.opacity = '0';
            setTimeout(() => {
                reviewItem.remove();
                
                // 检查是否还有评论
                const container = document.querySelector(`[id*="all-reviews-"] .review-list`);
                if (container && container.children.length === 0) {
                    container.innerHTML = '<div class="no-results">暂无评论</div>';
                }
            }, 300);
        } else {
            alert(data.error || '删除失败，请稍后重试');
        }
    })
    .catch(error => {
        console.error('删除评论失败:', error);
        alert('删除失败，请检查网络连接');
    });
}

// 返回详情视图
function hideAllReviews(dishId) {
    document.getElementById(`detail-body-${dishId}`).classList.remove('hidden');
    document.getElementById(`review-body-${dishId}`).classList.add('hidden');
}

// 辅助函数
function getCrowdLevelText(level) {
  const levels = {
    1: '非常空闲',
    2: '较空闲',
    3: '适中',
    4: '较密集',
    5: '非常密集'
  };
  return levels[level] || '未知';
}

function getQueueRatingText(rating) {
  const ratings = {
    1: '基本不排队',
    2: '排队较短',
    3: '排队适中',
    4: '排队较长',
    5: '排队很长'
  };
  const normalizedRating = Math.round(Number(rating));
  return ratings[normalizedRating] || '暂无评分';
}

function getPeopleIcons(rating) {
  const count = Math.round(Number(rating)) || 0;
  const maxPeople = 5;
  
  let icons = '';
  for (let i = 1; i <= maxPeople; i++) {
    if (i <= count) {
      icons += '<span class="person-icon"></span>'; // 橙色小人
    } else {
      icons += '<span class="person-icon empty"></span>'; // 灰色小人
    }
  }
  
  return `<span class="people-icons">${icons}</span>`;
}

// 简化关闭详情页 - 直接完全关闭
function closeDetailModal() {
  const modal = document.getElementById('detail-modal');
  
  // 直接完全关闭，不再处理历史记录
  modal.classList.add('hidden');
  detailHistory = [];
  
  // 清理历史状态
  if (window.history.state && window.history.state.detailPage) {
    history.replaceState(null, '', window.location.pathname);
  }
}

// 统一关闭模态框
function closeModal(modalId) {
  if (!modalId || modalId === 'detail-modal') {
    // 如果是详情模态框，使用专门的关闭函数
    closeDetailModal();
  } else {
    // 其他模态框直接关闭
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('hidden');
    }
  }
}

// 简化关闭事件监听 - 统一处理所有关闭按钮
document.addEventListener('click', e => {
    // 处理所有带data-close属性的元素
    if (e.target.matches('[data-close]')) {
        e.preventDefault();
        const modal = e.target.closest('.modal');
        if (modal) {
            const modalId = modal.id;
            if (modalId === 'detail-modal') {
                closeDetailModal();
            } else {
                modal.classList.add('hidden');
            }
        }
    }
    
    // 处理特定模态框的关闭按钮
    if (e.target.matches('#detail-modal .close-modal')) {
        e.preventDefault();
        closeDetailModal();
    }
    
    if (e.target.matches('#rating-modal .close-modal')) {
        e.preventDefault();
        document.getElementById('rating-modal').classList.add('hidden');
    }
    
    if (e.target.matches('#crowd-modal .close-modal')) {
        e.preventDefault();
        document.getElementById('crowd-modal').classList.add('hidden');
    }
});