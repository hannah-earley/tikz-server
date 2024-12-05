if (!onTikZReady) {
  window.onTikZReady = function(){
    console.log("All TikZ scripts loaded.");
  };
}

window.processTikZ = function(server, scale) {
  let preamble = "";
  let notReady = 0;

  function texError(error, scriptElement) {
    const div = document.createElement("div");
    div.className = "tikz-error";
    div.innerText = error;
    scriptElement.insertAdjacentElement('afterend', div);
    div.scrollTop = div.scrollHeight;
  }

  async function handleTexContent(content, scriptElement) {
    try {
      let formData = new FormData();
      formData.append("preamble", preamble);
      formData.append("source", content);
      if (scriptElement.hasAttribute("data-compile"))
        formData.append("compiles", scriptElement.getAttribute("data-compile"));
      if (scriptElement.hasAttribute("data-format"))
        formData.append("format", scriptElement.getAttribute("data-format"));
      
      const response = await fetch(server, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        texError(await response.text(), scriptElement);
      } else {
        const result = await response.blob();
        const mime = result.type;
        const imageURL = URL.createObjectURL(result);
        const scale2 = response.headers.get('X-TikZ-Scale') || scale;

        const img = document.createElement("img");
        img.onload = function() {
          const w = img.naturalWidth;
          let el;

          if (mime == "image/svg+xml") {
            el = document.createElement("object");
            el.type = "image/svg+xml";
            el.data = imageURL;
          } else {
            el = img;
          }

          el.className = "tikz";
          el.style.width = (w / scale2)+'em';
          scriptElement.replaceWith(el);
        };
        img.src = imageURL;
      }
    } catch (err) {
      texError("Unexpected error: "+err, scriptElement);
    }

    notReady -= 1;
    if (notReady == 0 && window.onTikZReady)
      onTikZReady();
  }

  document.addEventListener("DOMContentLoaded", () => {
    const preScripts = document.querySelectorAll('script[type="preamble"]');
    preScripts.forEach((script) => {
      const tikzContent = script.textContent;
      preamble += tikzContent;
      script.remove();
    });

    const texScripts = document.querySelectorAll('script[type="tex"], script[type="tikz"]');
    texScripts.forEach((script) => {
      let content = script.textContent;
      if (script.type == "tex") {
        // content = content;
      } else if (script.type == "tikz") {
        content = "\\begin{tikzpicture}"+content+"\\end{tikzpicture}";
      } else {
        texError("Unexpected error", scriptElement);
        return;
      }

      notReady += 1;
      handleTexContent(content, script);
    });
    
    if (notReady == 0 && window.onTikZReady)
      onTikZReady();
  });
};
