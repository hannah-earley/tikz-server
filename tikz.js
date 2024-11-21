window.processTikz = function(server) {
  server = server + '/png';

  let preamble = "";

  async function handleTikzContent(content, scriptElement) {
    console.log("TikZ content:", content);
    try {
      let formData = new FormData();
      formData.append("preamble", preamble);
      formData.append("source", "\\begin{tikzpicture}"+content+"\\end{tikzpicture}");
      const response = await fetch(server, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        const error = await response.text();
        const div = document.createElement("div");
        div.className = "tikz-error";
        div.innerText = error;
        scriptElement.insertAdjacentElement('afterend', div);
        div.scrollTop = div.scrollHeight;
      } else {
        const result = await response.blob();
        const imageURL = URL.createObjectURL(result);
        const img = document.createElement("img");
        img.onload = function() {
          const w = img.naturalWidth;
          const h = img.naturalHeight;
          img.style.width = (w / 100)+'em';
          img.style.height = (h / 100)+'em';
        };
        img.className = "tikz"
        img.src = imageURL;
        scriptElement.replaceWith(img);
      }
    } catch (err) {
      alert("Error!" + err);
      console.log(err)
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const tikzScripts = document.querySelectorAll('script[type="preamble"]');
    tikzScripts.forEach((script) => {
      const tikzContent = script.textContent;
      preamble += tikzContent;
      script.remove();
    });
  });

  document.addEventListener("DOMContentLoaded", () => {
    const tikzScripts = document.querySelectorAll('script[type="tikz"]');
    tikzScripts.forEach((script) => {
      const tikzContent = script.textContent;
      handleTikzContent(tikzContent, script);
    });
  });
}
