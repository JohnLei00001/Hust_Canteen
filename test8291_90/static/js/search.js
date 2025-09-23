let page = 1;
let total = 0;
let busy = false;

function buildQuery() {
  return {
    q: new URLSearchParams(location.search).get('q') || '',
    type: document.getElementById('filter-type').value,
    sort: document.getElementById('filter-sort').value,
    page: page
  };
}

function fetchAndRender(reset = true) {
  if (busy) return;
  busy = true;
  const params = new URLSearchParams(buildQuery());
  const box = document.getElementById('results');
  
  if (reset) {
    box.innerHTML = `
      <div class="loading-placeholder">
        <div class="skeleton-container" style="flex-direction: column; gap: 15px; align-items: stretch;">
          <div class="skeleton-card" style="max-width: 100%;">
            <div class="skeleton-image" style="height: 80px;"></div>
            <div class="skeleton-content">
              <div class="skeleton-line"></div>
              <div class="skeleton-line medium"></div>
            </div>
          </div>
          <div class="skeleton-card" style="max-width: 100%;">
            <div class="skeleton-image" style="height: 80px;"></div>
            <div class="skeleton-content">
              <div class="skeleton-line"></div>
              <div class="skeleton-line medium"></div>
            </div>
          </div>
          <div class="skeleton-card" style="max-width: 100%;">
            <div class="skeleton-image" style="height: 80px;"></div>
            <div class="skeleton-content">
              <div class="skeleton-line"></div>
              <div class="skeleton-line medium"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  fetch(`/api/search?${params}`)
    .then(r => r.json())
    .then(data => {
      total = data.total;
      renderItems(data.items, reset);
      busy = false;
    });
}

function getCrowdLevelText(level) {
  const levels = {
    1: '非常空闲',
    2: '较空闲',
    3: '适中',
    4: '较密集',
    5: '非常密集'
  };
  // 确保level是整数且在1-5范围内
  const normalizedLevel = Math.round(Number(level));
  return levels[normalizedLevel] || '未知';
}

function getQueueRatingText(rating) {
  const ratings = {
    1: '基本不排队',
    2: '排队较短',
    3: '排队适中',
    4: '排队较长',
    5: '排队很长'
  };
  // 确保rating是整数且在1-5范围内
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

function renderItems(items, reset) {
  const box = document.getElementById('results');
  if (reset) box.innerHTML = '';
  items.forEach(it => {
    const div = document.createElement('div');
    div.className = 'ranking-item';
    div.onclick = () => {
      if (it.type === 'dish') {
        showDetail('stall-dish', it.id);
      } else {
        showDetail(it.type, it.id);
      }
    };
    
    let ratingDisplay = '';
    if (it.type === 'canteen') {
      // 食堂类型显示拥挤度文字
      ratingDisplay = getCrowdLevelText(it.rating) || '—';
    } else if (it.type === 'stall') {
        // 窗口显示小人图标表示排队情况
        ratingDisplay = getPeopleIcons(it.rating);
      } else {
        // 菜品显示星级评分
        ratingDisplay = `★ ${it.rating || '—'}`;
      }
    
    div.innerHTML = `
      <div class="ranking-header">
        <span class="ranking-name">${it.name}</span>
        <span class="ranking-rating">${ratingDisplay}</span>
      </div>
      <div class="ranking-details">${it.location}${it.price ? ` | ¥${it.price}` : ''}</div>`;
    box.appendChild(div);
  });
  document.getElementById('load-more').classList.toggle('hidden', items.length === 0 || total <= page * 20);
}

function loadMore() {
  page += 1;
  fetchAndRender(false);
}

// 事件绑定
document.getElementById('search-form').addEventListener('submit', e => {
  e.preventDefault();
  const q = document.getElementById('search-input').value.trim();
  if (!q) return;
  history.replaceState(null, '', `?q=${encodeURIComponent(q)}`);
  page = 1;
  fetchAndRender(true);
});

['filter-type', 'filter-sort'].forEach(id =>
  document.getElementById(id).addEventListener('change', () => { page = 1; fetchAndRender(true); })
);

// 统一关闭弹窗（search.js / favorites.js 末尾）
document.addEventListener('click', e => {
  if (e.target.matches('[data-close]') || e.target.id === 'search-overlay') {
    const modal = document.getElementById('detail-modal');
    if (modal) modal.classList.add('hidden');
  }
});

// 首次加载
window.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(location.search);
  const q = urlParams.get('q') || '';
  if (q) {
    document.getElementById('search-input').value = q;
  }
  fetchAndRender(true);
});