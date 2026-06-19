// Global Theme Management
document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    const toggleBtn = document.getElementById("themeToggle");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const targetTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", targetTheme);
            localStorage.setItem("theme", targetTheme);
        });
    }
});

// Dinamik Gizlət/Göstər funksiyası
function toggleVisibility(id) {
    const element = document.getElementById(id);
    if (element.style.display === "none" || element.style.display === "") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}

// Groq Asinxron API çağırışı
async function fetchGroqSentence(word) {
    const btn = document.getElementById("aiBtn");
    const container = document.getElementById("aiSentenceContainer");
    
    btn.innerText = "Süni İntellekt Cümlə Qurur...";
    btn.disabled = true;

    try {
        const response = await fetch(`/api/generate-sentence?word=${encodeURIComponent(word)}`);
        if (!response.ok) throw new Error("API Xətası");
        const data = await response.json();
        
        container.innerHTML = `
            <div class="card" style="border-color: #9b59b6; background: rgba(155, 89, 182, 0.02);">
                <h4 style="color: #9b59b6; margin-bottom: 8px;">🔮 Groq AI Kontekst</h4>
                <p style="font-size: 1.1rem; margin-bottom: 12px;"><strong>EN:</strong> ${data.sentence}</p>
                <button class="btn" style="padding: 6px 12px; font-size: 0.85rem; width: auto;" onclick="toggleVisibility('dynamicAiTrans')">Tərcüməni Göstər</button>
                <div id="dynamicAiTrans" class="translation-box" style="margin-top: 10px;">
                    <strong>AZ:</strong> ${data.translation}
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<p style="color: var(--danger);">Xəta: Süni intellekt cavab vermədi.</p>`;
    } finally {
        btn.innerText = "Groq AI-dan Yeni Cümlə Al";
        btn.disabled = false;
    }
}