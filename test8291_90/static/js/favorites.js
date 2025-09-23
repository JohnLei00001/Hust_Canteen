document.addEventListener('DOMContentLoaded', () => {
  loadFavorites('');
  document.getElementById('search-form').addEventListener('submit', e => {
    e.preventDefault();
    loadFavorites(document.getElementById('search-input').value.trim());
  });
});

function loadFavorites(q) {
  const container = document.getElementById('favorites-container');
  container.innerHTML = `
    <div class="loading-placeholder" style="width: 100%; padding: 40px 20px;">
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto;">
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
  fetch(`/api/my-favorites?q=${encodeURIComponent(q)}`)
    .then(res => res.json())
    .then(list => renderFavoriteList(list))
    .catch(() => { container.innerHTML = '<div class="error">加载失败</div>'; });
}

function renderFavoriteList(items) {
  const box = document.getElementById('favorites-container');
  box.innerHTML = '';
  if (!items.length) {
    box.innerHTML = '<div class="no-results">还没有收藏任何菜品哦～</div>';
    return;
  }
  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    card.style.marginBottom = '20px';
    card.onclick = () => showDetail('stall-dish', item.id);
    card.innerHTML = `
      <div class="recommendation-image" style="background-image:url('/static/images/dish-default.jpg')"></div>
      <div class="recommendation-info">
        <h3 class="recommendation-title">${item.name}</h3>
        <div class="recommendation-desc">${item.location}</div>
        <div class="recommendation-meta">
          <span class="recommendation-rating">★ ${item.rating}</span>
          <span>¥${item.price}</span>
        </div>
      </div>`;
    box.appendChild(card);
  });
}

// 统一关闭弹窗（search.js / favorites.js 末尾）
document.addEventListener('click', e => {
  if (e.target.matches('[data-close]') || e.target.id === 'search-overlay') {
    const modal = document.getElementById('detail-modal');
    if (modal) modal.classList.add('hidden');
  }
});
