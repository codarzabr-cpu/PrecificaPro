
document.addEventListener("DOMContentLoaded", () => {
    // Menu responsivo para telas menores.
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

    if (sidebar && menuToggle) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", (event) => {
            if (
                window.innerWidth <= 900 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !menuToggle.contains(event.target)
            ) {
                sidebar.classList.remove("open");
            }
        });
    }

    // Pesquisa instantânea nas tabelas.
    const searchInput = document.getElementById("tableSearch");
    const table = document.getElementById("searchTable");

    if (searchInput && table) {
        searchInput.addEventListener("input", () => {
            const termo = searchInput.value
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase()
                .trim();

            table.querySelectorAll("tbody tr").forEach((linha) => {
                const texto = linha.innerText
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase();

                linha.hidden = !texto.includes(termo);
            });
        });
    }

    // Fecha notificações depois de alguns segundos.
    document.querySelectorAll(".flash").forEach((mensagem) => {
        window.setTimeout(() => {
            mensagem.style.transition = "opacity .3s ease";
            mensagem.style.opacity = "0";

            window.setTimeout(() => mensagem.remove(), 350);
        }, 4500);
    });
});
