document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        console.error("Error fetching data:", error);
        document.getElementById('indices-container').innerHTML = '<div class="loader"><span>ERROR LOADING DATA</span></div>';
        document.getElementById('sectors-container').innerHTML = '<div class="loader"><span>ERROR LOADING DATA</span></div>';
    }
}

function renderDashboard(data) {
    if (data.market_date && data.market_date !== "알 수 없음") {
        const dateStr = `[ ${data.market_date} CLOSE ]`;
        
        const iDateEl = document.getElementById('indices-date');
        if (iDateEl) iDateEl.textContent = dateStr;
        
        const sDateEl = document.getElementById('sectors-date');
        if (sDateEl) sDateEl.textContent = dateStr;
    }

    const indicesContainer = document.getElementById('indices-container');
    
    // Render Indices
    indicesContainer.innerHTML = '';
    data.indices.forEach((obj, index) => {
        const valClass = obj.change > 0 ? 'val-pos' : (obj.change < 0 ? 'val-neg' : 'val-neu');
        const icon = obj.change > 0 ? '▲' : (obj.change < 0 ? '▼' : '−');
        
        const div = document.createElement('div');
        div.className = `index-card`;
        div.style.animationDelay = `${index * 0.1}s`; // Stagger animation
        
        div.innerHTML = `
            <div class="index-name">${obj.name}</div>
            <div class="index-value ${valClass}">
                <span class="indicator">${icon}</span> 
                ${obj.change > 0 ? '+' : ''}${obj.change.toFixed(2)}%
            </div>
        `;
        indicesContainer.appendChild(div);
    });

    // Cache sectors for sorting/filtering
    cachedSectors = data.sectors;
    renderSectors();
}

let currentSort = 'desc'; // 'desc', 'asc', 'name'
let currentView = 'all';  // 'all', 'compact'
let cachedSectors = [];

function getColumnCount() {
    const width = window.innerWidth;
    if (width <= 480) return 1;
    if (width <= 768) return 2;
    if (width <= 1100) return 3;
    if (width <= 1400) return 4;
    return 5;
}

function renderSectors() {
    const sectorsContainer = document.getElementById('sectors-container');
    sectorsContainer.innerHTML = '';
    
    const numCols = getColumnCount();
    const boardCols = [];
    
    for (let i = 0; i < numCols; i++) {
        const col = document.createElement('div');
        col.className = 'board-column';
        col.id = `board-col-${i+1}`;
        sectorsContainer.appendChild(col);
        boardCols.push(col);
    }

    let sectorsToRender = [...cachedSectors];

    // Apply User Sort
    if (currentSort === 'desc') {
        sectorsToRender.sort((a, b) => b.change - a.change);
    } else if (currentSort === 'asc') {
        sectorsToRender.sort((a, b) => a.change - b.change);
    } else {
        sectorsToRender.sort((a, b) => a.name.localeCompare(b.name, 'ko'));
    }

    sectorsToRender.forEach((sector, i) => {
        const panel = document.createElement('div');
        panel.className = 'sector-panel';
        panel.style.animationDelay = `${(i % numCols) * 0.1 + Math.floor(i / numCols) * 0.05}s`; // Diagonal stagger effect
        
        const sIcon = sector.change > 0 ? '▲' : (sector.change < 0 ? '▼' : '−');
        const sValClass = sector.change > 0 ? 'val-pos' : (sector.change < 0 ? 'val-neg' : 'val-neu');

        // Header
        const header = document.createElement('div');
        header.className = 'sector-header';
        header.innerHTML = `
            <div class="sector-name">${sector.name}</div>
            <div class="sector-val ${sValClass}">${sIcon} ${sector.change > 0 ? '+' : ''}${sector.change.toFixed(2)}%</div>
        `;
        panel.appendChild(header);
        
        // Themes Truncation
        let themesToRender = sector.themes;
        if (currentView === 'compact' && themesToRender.length > 3) {
            let topMovers = [...themesToRender].sort((a, b) => Math.abs(b.change) - Math.abs(a.change)).slice(0, 3);
            topMovers.sort((a, b) => b.change - a.change);
            themesToRender = topMovers;
        }

        const themeList = document.createElement('div');
        themeList.className = 'theme-list';

        themesToRender.forEach(theme => {
            const row = document.createElement('div');
            
            const icon = theme.change > 0 ? '▲' : (theme.change < 0 ? '▼' : '−');
            let valClass = theme.change > 0 ? 'val-pos' : (theme.change < 0 ? 'val-neg' : 'val-neu');
            
            row.className = `theme-row`;
            
            // Strong Highlights
            if (theme.change >= 3) {
                row.classList.add('row-pos-strong');
            } else if (theme.change <= -3) {
                row.classList.add('row-neg-strong');
            }
            
            row.innerHTML = `
                <div class="theme-name"><span class="indicator">${icon}</span> ${theme.name}</div>
                <div class="theme-val ${valClass}">${theme.change > 0 ? '+' : ''}${theme.change.toFixed(2)}%</div>
            `;
            
            themeList.appendChild(row);
        });

        panel.appendChild(themeList);
        boardCols[i % numCols].appendChild(panel);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const sortBtn = document.getElementById('sort-btn');
    if (sortBtn) {
        sortBtn.addEventListener('click', () => {
            if (currentSort === 'desc') {
                currentSort = 'asc';
                sortBtn.innerHTML = '정렬: 낮은 순 <span class="btn-icon">▼</span>';
            } else if (currentSort === 'asc') {
                currentSort = 'name';
                sortBtn.innerHTML = '정렬: 이름 순 <span class="btn-icon">🔠</span>';
            } else {
                currentSort = 'desc';
                sortBtn.innerHTML = '정렬: 높은 순 <span class="btn-icon">▲</span>';
            }
            if (cachedSectors.length > 0) renderSectors();
        });
    }

    const filterBtn = document.getElementById('filter-btn');
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            if (currentView === 'all') {
                currentView = 'compact';
                filterBtn.innerHTML = '보기: 하위 3개 요약 <span class="btn-icon">✂️</span>';
            } else {
                currentView = 'all';
                filterBtn.innerHTML = '보기: 전체 뷰 <span class="btn-icon">👁️</span>';
            }
            if (cachedSectors.length > 0) renderSectors();
        });
    }

    let currentCols = getColumnCount();
    window.addEventListener('resize', () => {
        const newCols = getColumnCount();
        if (newCols !== currentCols) {
            currentCols = newCols;
            if (cachedSectors.length > 0) renderSectors();
        }
    });
});
