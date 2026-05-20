document.addEventListener("DOMContentLoaded", () => {
    const mensajes = document.querySelectorAll(".alerta");

    mensajes.forEach((mensaje) => {
        setTimeout(() => {
            mensaje.style.opacity = "0";
            mensaje.style.transition = "opacity .5s";
            setTimeout(() => mensaje.remove(), 500);
        }, 3500);
    });
});
