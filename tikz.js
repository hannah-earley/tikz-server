window.processTikz = function(server) {
  server = server + '/png';

  async function handleTikzContent(content, scriptElement) {
    console.log("TikZ content:", content);
    try {
      let formData = new FormData();
      formData.append("source", "\\begin{tikzpicture}"+content+"\\end{tikzpicture}");
      const response = await fetch(server, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const result = await response.blob();
      const imageURL = URL.createObjectURL(result);
      const img = document.createElement("img");
      img.onload = function() {
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        img.width = w * 0.2;
        img.height = h * 0.2;
      };
      img.className = "tikz"
      img.src = imageURL;
      scriptElement.replaceWith(img);
    } catch (err) {
      alert("Error!" + err);
      console.log(err)
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const tikzScripts = document.querySelectorAll('script[type="tikz"]');
    tikzScripts.forEach((script) => {
      const tikzContent = script.textContent;
      handleTikzContent(tikzContent, script);
    });
  });
}
