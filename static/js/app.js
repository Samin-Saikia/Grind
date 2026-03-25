// Global app utilities

async function loadProfile() {
  try {
    const res = await fetch('/api/profile');
    const data = await res.json();
    // Update streak
    const sc = document.getElementById('streak-count');
    if (sc) sc.textContent = data.profile.day_streak || '0';

    // Show milestones
    if (data.milestones && data.milestones.length > 0) {
      showMilestone(data.milestones[0]);
      await fetch('/api/milestones/seen', { method: 'POST' });
    }
    return data;
  } catch(e) { return null; }
}

function showMilestone(m) {
  const toast = document.getElementById('milestone-toast');
  if (!toast) return;
  toast.innerHTML = `<div class="milestone-toast-title">◆ ${m.type === 'level_up' ? 'Level Up' : 'Breakthrough'}</div>
    <div class="milestone-toast-body">${m.description}</div>`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 6000);
}

function mdToHtml(text) {
  if (!text) return '';
  return text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/gs, '<ul>$&</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])(.+)$/gm, (m) => m.startsWith('<') ? m : `<p>${m}</p>`);
}

function timeAgo(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

function typeColors(type) {
  const map = { learn: '#4a9eff', build: '#e8ff4a', research: '#9b4aff', reflect: '#4affd4' };
  return map[type] || '#5a5550';
}

document.addEventListener('DOMContentLoaded', loadProfile);
