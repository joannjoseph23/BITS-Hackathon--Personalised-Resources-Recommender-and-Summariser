// Handles file upload and extraction
async function handleUpload() {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    const outputDiv = document.getElementById('extractedText');
  
    if (!file) {
      alert('Please select a PDF or PPTX file to upload.');
      return;
    }
  
    const fileName = file.name.toLowerCase();
  
    if (fileName.endsWith('.pdf')) {
      const text = await extractTextFromPDF(file);
      outputDiv.textContent = text;
    } else if (fileName.endsWith('.pptx')) {
      const text = await extractTextFromPPTX(file);
      outputDiv.textContent = text;
    } else {
      alert('Unsupported file type.');
    }
  }
  
  // Extract text from PDF using pdf.js
  async function extractTextFromPDF(file) {
    const reader = new FileReader();
    return new Promise((resolve) => {
      reader.onload = async function() {
        const typedarray = new Uint8Array(this.result);
        const pdfjsLib = await import('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.7.107/pdf.min.mjs');
        const pdf = await pdfjsLib.getDocument(typedarray).promise;
  
        let fullText = '';
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const content = await page.getTextContent();
          const strings = content.items.map(item => item.str).join(' ');
          fullText += strings + '\n\n';
        }
        resolve(fullText);
      };
      reader.readAsArrayBuffer(file);
    });
  }
  
  // Extract text from PPTX using PptxGenJS (limited support)
  async function extractTextFromPPTX(file) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = function(event) {
        const zip = new JSZip();
        zip.loadAsync(event.target.result).then((contents) => {
          let textPromises = [];
  
          Object.keys(contents.files).forEach((filename) => {
            if (filename.match(/ppt\/slides\/slide[0-9]+\.xml/)) {
              textPromises.push(
                contents.files[filename].async("string").then((data) => {
                  const matches = data.match(/<a:t>(.*?)<\/a:t>/g);
                  return matches ? matches.map(t => t.replace(/<\/?a:t>/g, '')).join(' ') : '';
                })
              );
            }
          });
  
          Promise.all(textPromises).then(texts => {
            resolve(texts.join('\n\n'));
          });
        });
      };
      reader.readAsArrayBuffer(file);
    });
  }
  