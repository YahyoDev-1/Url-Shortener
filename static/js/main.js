// Shortly — umumiy JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Xabarlarni yopish tugmasi
    document.querySelectorAll('.msg-close').forEach((btn) => {
        btn.addEventListener('click', () => hideMessage(btn.closest('.msg-item')));
    });

    // Xabarlar 5 soniyadan keyin o'zi yo'qoladi
    document.querySelectorAll('.msg-item').forEach((msg) => {
        setTimeout(() => hideMessage(msg), 5000);
    });
});

function hideMessage(el) {
    if (!el) return;
    el.classList.add('msg-hide');
    setTimeout(() => el.remove(), 300);
}
