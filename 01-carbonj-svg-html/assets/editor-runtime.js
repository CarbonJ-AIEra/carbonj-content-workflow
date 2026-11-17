(() => {
  const slides = [...document.querySelectorAll('.deck-slide')];
  const editButton = document.querySelector('#edit-toggle');
  const longPage = document.body.dataset.layout === 'long';
  const fillInput = document.querySelector('#fill-value');
  const saveButton = document.querySelector('#download-html');
  const svgButton = document.querySelector('#download-svg');
  const prevButton = document.querySelector('#prev-slide');
  const nextButton = document.querySelector('#next-slide');
  const counter = document.querySelector('#slide-counter');
  let index = 0;
  let editing = false;
  let selectedText = null;
  let selectedShape = null;
  let inlineEditor = null;

  const linesOf = el => {
    const tspans = [...el.querySelectorAll(':scope > tspan')];
    return tspans.length ? tspans.map(t => t.textContent).join('\n') : el.textContent;
  };
  const setLines = (el, value) => {
    const lines = value.split('\n');
    const spans = [...el.querySelectorAll(':scope > tspan')];
    const firstSpan = spans[0];
    const x = el.getAttribute('x') || firstSpan?.getAttribute('x') || '0';
    const gap = el.dataset.lineHeight || spans[1]?.getAttribute('dy') || '1.2em';
    el.replaceChildren(...lines.map((line, i) => {
      const span = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
      span.setAttribute('x', x);
      span.setAttribute('dy', i === 0 ? '0' : gap);
      span.textContent = line;
      return span;
    }));
  };
  const commitInlineEdit = () => {
    if (!inlineEditor) return;
    if (selectedText) setLines(selectedText, inlineEditor.value);
    inlineEditor.remove();
    inlineEditor = null;
    selectedText?.classList.remove('is-selected');
    selectedText = null;
  };
  const openInlineEdit = text => {
    commitInlineEdit();
    selectedShape?.classList.remove('is-selected');
    selectedShape = null;
    selectedText = text;
    text.classList.add('is-selected');
    const box = text.getBoundingClientRect();
    const style = getComputedStyle(text);
    const matrix = text.getScreenCTM();
    const scaleY = matrix ? Math.hypot(matrix.c, matrix.d) : 1;
    const fontPx = parseFloat(style.fontSize) * scaleY;
    const lineCount = Math.max(1, linesOf(text).split('\n').length);
    inlineEditor = document.createElement('textarea');
    inlineEditor.className = 'inline-svg-editor';
    inlineEditor.setAttribute('aria-label', '在画布原位编辑文字');
    inlineEditor.value = linesOf(text);
    Object.assign(inlineEditor.style, {
      position: 'fixed', left: `${Math.max(0, box.left - 3)}px`, top: `${Math.max(0, box.top - 4)}px`,
      width: `${Math.max(90, box.width + 18)}px`, height: `${Math.max(fontPx * lineCount * 1.3, box.height + 16)}px`,
      padding: '2px 4px', margin: '0', resize: 'none', overflow: 'hidden', zIndex: '1000',
      background: 'rgba(255,253,248,.96)', border: '2px dashed #7185bd', borderRadius: '3px',
      outline: 'none', color: style.fill, fontFamily: style.fontFamily, fontSize: `${fontPx}px`,
      fontWeight: style.fontWeight, lineHeight: `${fontPx * 1.2}px`, textAlign: style.textAnchor === 'middle' ? 'center' : style.textAnchor === 'end' ? 'right' : 'left'
    });
    document.body.append(inlineEditor);
    inlineEditor.addEventListener('input', () => setLines(text, inlineEditor.value));
    inlineEditor.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); inlineEditor.blur(); }
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); inlineEditor.blur(); }
    });
    inlineEditor.addEventListener('blur', commitInlineEdit, { once: true });
    inlineEditor.focus();
    inlineEditor.setSelectionRange(inlineEditor.value.length, inlineEditor.value.length);
  };
  const setEditing = value => {
    editing = value;
    document.body.classList.toggle('is-editing', editing);
    editButton?.setAttribute('aria-pressed', String(editing));
    if (editButton) editButton.textContent = editing ? '完成编辑' : '编辑内容';
    document.querySelectorAll('[data-editable-html]').forEach(element => {
      element.contentEditable = String(editing);
    });
    if (fillInput) fillInput.disabled = !editing || !selectedShape;
    if (!editing) {
      commitInlineEdit();
      selectedShape?.classList.remove('is-selected');
      selectedShape = null;
    }
  };
  const rgbToHex = value => {
    const parts = value.match(/[\d.]+/g)?.slice(0, 3).map(Number);
    return parts?.length === 3 ? '#' + parts.map(v => Math.round(v).toString(16).padStart(2, '0')).join('') : '#ffffff';
  };
  const showSlide = n => {
    commitInlineEdit();
    if (longPage || !slides.length) return;
    index = (n + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.hidden = i !== index;
      slide.classList.toggle('is-active', i === index);
    });
    if (counter) counter.textContent = `${index + 1} / ${slides.length}`;
  };

  document.addEventListener('click', event => {
    const canvas = event.target.closest('.deck-slide');
    if (longPage && canvas) index = slides.indexOf(canvas);
    if (!editing || event.target.closest('#deck-toolbar,.inline-svg-editor')) return;
    const text = event.target.closest('[data-editable-text]');
    const shape = event.target.closest('[data-editable-shape]');
    if (text) {
      openInlineEdit(text);
    } else if (shape) {
      commitInlineEdit();
      selectedShape?.classList.remove('is-selected');
      selectedShape = shape;
      selectedShape.classList.add('is-selected');
      if (fillInput) {
        fillInput.value = rgbToHex(getComputedStyle(shape).fill);
        fillInput.disabled = false;
      }
    } else {
      commitInlineEdit();
      selectedShape?.classList.remove('is-selected');
      selectedShape = null;
      if (fillInput) fillInput.disabled = true;
    }
  });

  fillInput?.addEventListener('input', () => {
    if (selectedShape) selectedShape.setAttribute('fill', fillInput.value);
  });
  editButton?.addEventListener('click', () => setEditing(!editing));
  prevButton?.addEventListener('click', () => showSlide(index - 1));
  nextButton?.addEventListener('click', () => showSlide(index + 1));
  document.addEventListener('keydown', event => {
    if (longPage || event.target.closest('textarea,input,[contenteditable="true"]')) return;
    if (['ArrowRight', 'PageDown'].includes(event.key)) showSlide(index + 1);
    if (['ArrowLeft', 'PageUp'].includes(event.key)) showSlide(index - 1);
    if (event.key === 'Home') showSlide(0);
    if (event.key === 'End') showSlide(slides.length - 1);
  });

  const download = (name, mime, contents) => {
    const url = URL.createObjectURL(new Blob([contents], { type: mime }));
    const link = Object.assign(document.createElement('a'), { href: url, download: name });
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  svgButton?.addEventListener('click', () => {
    commitInlineEdit();
    const svg = slides[index]?.querySelector('svg');
    if (!svg) return;
    const copy = svg.cloneNode(true);
    copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const sourceNodes = [svg, ...svg.querySelectorAll('*')];
    const copyNodes = [copy, ...copy.querySelectorAll('*')];
    sourceNodes.forEach((source, i) => {
      const target = copyNodes[i];
      const style = getComputedStyle(source);
      if (source.hasAttribute('fill') || source.hasAttribute('data-editable-shape')) target.setAttribute('fill', style.fill);
      if (source.hasAttribute('stroke') || style.stroke !== 'none') target.setAttribute('stroke', style.stroke);
      if (source.localName === 'text') {
        target.setAttribute('font-family', style.fontFamily);
        target.setAttribute('font-size', style.fontSize);
        target.setAttribute('font-weight', style.fontWeight);
        target.setAttribute('fill', style.fill);
        target.removeAttribute('class');
      }
    });
    download(`slide-${String(index + 1).padStart(2, '0')}.svg`, 'image/svg+xml;charset=utf-8', new XMLSerializer().serializeToString(copy));
  });
  saveButton?.addEventListener('click', () => {
    commitInlineEdit();
    setEditing(false);
    const copy = document.documentElement.cloneNode(true);
    const embeddedCopies = [...copy.querySelectorAll('iframe[srcdoc]')];
    document.querySelectorAll('iframe[srcdoc]').forEach((frame, frameIndex) => {
      try {
        const embeddedDocument = frame.contentDocument;
        if (!embeddedDocument || !embeddedCopies[frameIndex]) return;
        const embeddedCopy = embeddedDocument.documentElement.cloneNode(true);
        embeddedCopy.querySelectorAll('.inline-svg-editor').forEach(element => element.remove());
        embeddedCopy.querySelectorAll('[contenteditable]').forEach(element => element.removeAttribute('contenteditable'));
        embeddedCopy.querySelectorAll('.is-selected').forEach(element => element.classList.remove('is-selected'));
        embeddedCopy.querySelector('body')?.classList.remove('is-editing');
        const embeddedEditButton = embeddedCopy.querySelector('#edit-toggle');
        if (embeddedEditButton) {
          embeddedEditButton.textContent = '编辑内容';
          embeddedEditButton.setAttribute('aria-pressed', 'false');
        }
        embeddedCopies[frameIndex].setAttribute('srcdoc', '<!doctype html>\n' + embeddedCopy.outerHTML);
      } catch (error) {
        // Keep the original srcdoc when a frame is inaccessible.
      }
    });
    copy.querySelectorAll('.is-selected').forEach(el => el.classList.remove('is-selected'));
    copy.querySelectorAll('script[data-runtime]').forEach(script => script.remove());
    const runtime = document.querySelector('script[data-runtime]');
    if (runtime) copy.body.append(runtime.cloneNode(true));
    download(longPage ? 'editable-svg-page.html' : 'editable-svg-deck.html', 'text/html;charset=utf-8', '<!doctype html>\n' + copy.outerHTML);
  });
  if (fillInput) fillInput.disabled = true;
  showSlide(0);
})();
