window.processTikz = function(server) {
  const png = true;
  let scale = 10;
  if (png) {
    server = server + '/png';
    scale = 100;
  } else {
    server = server + '/svg';
  }

  let preamble = "";
  let notReady = 0;

  async function handleTexContent(content, scriptElement) {
    try {
      let formData = new FormData();
      formData.append("preamble", preamble);
      formData.append("source", content);
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
          img.style.width = (w / scale)+'em';
        };
        img.className = "tikz"
        img.src = imageURL;
        scriptElement.replaceWith(img);
      }
    } catch (err) {
      alert("Error!" + err);
      console.log(err);
    }

    notReady -= 1;
    if (notReady == 0 && window.onTikzReady)
      onTikzReady();
  }

  async function handleTikzContent(content, scriptElement) {
    handleTexContent("\\begin{tikzpicture}"+content+"\\end{tikzpicture}", scriptElement);
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
      notReady += 1;
      const tikzContent = script.textContent;
      handleTikzContent(tikzContent, script);
    });
  });

  document.addEventListener("DOMContentLoaded", () => {
    const tikzScripts = document.querySelectorAll('script[type="tex"]');
    tikzScripts.forEach((script) => {
      notReady += 1;
      const tikzContent = script.textContent;
      handleTexContent(tikzContent, script);
    });
  });
}
