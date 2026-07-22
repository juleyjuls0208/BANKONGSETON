  /* ---------- THREE.JS: glossy liquid-glass RFID card ---------- */
  (async () => {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    try {
      if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (_) {} }
      const THREE = await import('https://esm.sh/three@0.161.0');
      const TEX = THREE;

      const renderer = new TEX.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
      renderer.outputColorSpace = TEX.SRGBColorSpace;
      renderer.toneMapping = TEX.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.08;

      const scene = new TEX.Scene();
      const camera = new TEX.PerspectiveCamera(34, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
      camera.position.set(0, 0, 5.6);

      // ---- environment for glossy reflections ----
      const pmrem = new TEX.PMREMGenerator(renderer);
      const envScene = new TEX.Scene();
      const grad = (() => {
        const c = document.createElement('canvas'); c.width = 16; c.height = 256;
        const x = c.getContext('2d');
        const g = x.createLinearGradient(0, 0, 0, 256);
        g.addColorStop(0.00, '#fbe6c0'); g.addColorStop(0.30, '#9fb4d8');
        g.addColorStop(0.52, '#2b2f3a'); g.addColorStop(0.75, '#e9c97e');
        g.addColorStop(1.00, '#1a1c22');
        x.fillStyle = g; x.fillRect(0, 0, 16, 256);
        const t = new TEX.CanvasTexture(c); t.mapping = TEX.EquirectangularReflectionMapping;
        return t;
      })();
      const envRT = pmrem.fromEquirectangular(grad);
      scene.environment = envRT.texture;

      // ---- lights ----
      scene.add(new TEX.HemisphereLight(0xffffff, 0x101216, 0.6));
      const key = new TEX.DirectionalLight(0xfff3df, 2.2); key.position.set(2.4, 3.2, 4); scene.add(key);
      const fill = new TEX.DirectionalLight(0x9ec5ff, 0.7); fill.position.set(-3, -1, 2); scene.add(fill);
      const warm = new TEX.PointLight(0xffd9a0, 7, 30); warm.position.set(-2.6, 1.6, 3); scene.add(warm);
      const cool = new TEX.PointLight(0x9ec5ff, 4, 30); cool.position.set(2.8, -1.2, 2.4); scene.add(cool);
      const rim = new TEX.PointLight(0xffe9bf, 5, 24); rim.position.set(0, 2.6, -3); scene.add(rim);

      // ---- card face: glossy liquid-glass gold ----
      function makeCardTexture() {
        const c = document.createElement('canvas'); c.width = 1024; c.height = 646;
        const x = c.getContext('2d');
        const g = x.createLinearGradient(0, 0, c.width, c.height);
        g.addColorStop(0, '#E7C884'); g.addColorStop(0.45, '#D2AE63'); g.addColorStop(1, '#B98F49');
        x.fillStyle = g; x.fillRect(0, 0, c.width, c.height);
        const sh = x.createLinearGradient(0, 0, c.width * 0.7, c.height * 0.7);
        sh.addColorStop(0, 'rgba(255,255,255,0.30)'); sh.addColorStop(1, 'rgba(255,255,255,0)');
        x.fillStyle = sh; x.fillRect(0, 0, c.width, c.height);
        // soft moving sheen hints (static, subtle)
        const sh2 = x.createRadialGradient(c.width * 0.2, c.height * 0.25, 10, c.width * 0.2, c.height * 0.25, 460);
        sh2.addColorStop(0, 'rgba(255,255,255,0.16)'); sh2.addColorStop(1, 'rgba(255,255,255,0)');
        x.fillStyle = sh2; x.fillRect(0, 0, c.width, c.height);
        const m = 20, br = 90;
        x.strokeStyle = 'rgba(255,238,196,0.95)'; x.lineWidth = 4;
        x.beginPath();
        x.moveTo(m + br, m); x.lineTo(c.width - m - br, m); x.quadraticCurveTo(c.width - m, m, c.width - m, m + br);
        x.lineTo(c.width - m, c.height - m - br); x.quadraticCurveTo(c.width - m, c.height - m, c.width - m - br, c.height - m);
        x.lineTo(m + br, c.height - m); x.quadraticCurveTo(m, c.height - m, m, c.height - m - br);
        x.lineTo(m, m + br); x.quadraticCurveTo(m, m, m + br, m);
        x.stroke();
        const tex = new TEX.CanvasTexture(c);
        tex.colorSpace = TEX.SRGBColorSpace; tex.anisotropy = 8;
        return tex;
      }

      const w = 1.5, h = 0.945, r = 0.13;
      const shape = new TEX.Shape();
      shape.moveTo(-w + r, -h);
      shape.lineTo(w - r, -h); shape.quadraticCurveTo(w, -h, w, -h + r);
      shape.lineTo(w, h - r); shape.quadraticCurveTo(w, h, w - r, h);
      shape.lineTo(-w + r, h); shape.quadraticCurveTo(-w, h, -w, h - r);
      shape.lineTo(-w, -h + r); shape.quadraticCurveTo(-w, -h, -w + r, -h);
      const geo = new TEX.ExtrudeGeometry(shape, {
        depth: 0.06, bevelEnabled: true, bevelThickness: 0.025, bevelSize: 0.025, bevelSegments: 5, steps: 1,
      });
      geo.center();

      const tex = makeCardTexture();
      // glossy liquid-glass: high clearcoat, low roughness, reflective
      const glassMat = new TEX.MeshPhysicalMaterial({
        map: tex, color: 0xffffff, metalness: 0.55, roughness: 0.14,
        clearcoat: 1.0, clearcoatRoughness: 0.08, envMapIntensity: 1.5,
        transmission: 0.0, reflectivity: 1.0,
      });
      const card = new TEX.Mesh(geo, glassMat);
      scene.add(card);

      // thin inner glass highlight ring (fake liquid edge)
      const edgeGeo = new TEX.Shape();
      const ew = w - 0.015, eh = h - 0.015, er = r - 0.01;
      edgeGeo.moveTo(-ew + er, -eh);
      edgeGeo.lineTo(ew - er, -eh); edgeGeo.quadraticCurveTo(ew, -eh, ew, -eh + er);
      edgeGeo.lineTo(ew, eh - er); edgeGeo.quadraticCurveTo(ew, eh, ew - er, eh);
      edgeGeo.lineTo(-ew + er, eh); edgeGeo.quadraticCurveTo(-ew, eh, -ew, eh - er);
      edgeGeo.lineTo(-ew, -eh + er); edgeGeo.quadraticCurveTo(-ew, -eh, -ew + er, -eh);
      const hole = new TEX.Path(); hole.moveTo(-w + 0.02, -h + 0.02);
      hole.lineTo(w - 0.02, -h + 0.02); hole.lineTo(w - 0.02, h - 0.02); hole.lineTo(-w + 0.02, h - 0.02); hole.lineTo(-w + 0.02, -h + 0.02);
      edgeGeo.holes.push(hole);
      const edge = new TEX.Mesh(new TEX.ExtrudeGeometry(edgeGeo, { depth: 0.062, bevelEnabled: false, steps: 1 }),
        new TEX.MeshBasicMaterial({ color: 0xfff0cf, transparent: true, opacity: 0.35 }));
      edge.position.z = 0; card.add(edge);

      // ---- centered Seton crest (baked data-URI, monochrome) ----
      try {
        const logoTex = await new Promise((res, rej) => {
          const img = new Image();
          img.onload = () => {
            const lw = img.naturalWidth, lh = img.naturalHeight;
            const cv = document.createElement('canvas'); cv.width = lw; cv.height = lh;
            const cx2 = cv.getContext('2d');
            cx2.clearRect(0, 0, lw, lh); cx2.drawImage(img, 0, 0, lw, lh);
            const t = new TEX.CanvasTexture(cv); t.colorSpace = TEX.SRGBColorSpace; t.anisotropy = 8; res(t);
          };
          img.onerror = rej;
          img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAPwAAADcCAYAAABUB8xRAAB+aUlEQVR4nO2dBZiU5frGf990bnexS3d3CAiiICaoYB67j+eYRz0ez99jd3cnoCKioiIqEiLdndtd0/39r/ebBQuVXTZml725Zpmdnfnmq/t9n/eJ+4F2tKMd7WhHO9rRjna0ox3taEc72tEaILX0DrTj95ALjtcje5ORSCfkiYFQCqgTwWsm5DUhqazibYAJiAZqAHf4wyEbKr0b9E4IloKqFJWhBpl8JG2FlLHY137Oj120E74FIecPMSIHuiGH+iDJ3Qg5uiEHsoEsZE8CSCpkXx23xaUK1T3/K4j3qn7+nKQTz/1I+kokTR6S4QBycAcq4w4ky1Yk7Y72geDYQDvhmxFywbg0QrZhyN4RyJ6hhFw9IZCIHACCdSStuySSOkxYSaojrXgeCv9ZeUsd8aVfjgFS+LnyUIFc97syUIjnwbrn4iG2rwp/j6QvQTJsRWVeDaoVyIGVUofNpc15btrRPGgnfBNCzh+hQ/aMRvZNJGQfi+wbjOzRHSIgGmUSV56rQqAOhh8qQe662TmoDpM2qIKg+KiEJyQpn3bJEtVBiFODQXk/GMRnxbY0AVCJbQleC6LL4QEgJLapCW9PPFdeF38XD+r2SeNBMq1CFfU96ujvkQNLpcwVYqfb0crRTvhGhlw4SUuoZgrB2tMI2U9Edqf9THAxm6p/JqSmjtwhNfi02Lx6Cjw6cj0GCj069vu01Pj0lPrVlAZUeAI6PEEVrpCk8NghS1QFIUENxjrCm1QyRnUIvcZHijZIoiZEvN5Dji5AisFLR4OXDL0Xs94HOl94XwTx/RoIaOosAjEI1Fkdkl4sCQ4gGRegiv4EOfCd1GFTO/lbKdoJ30iQ80eNI1g8E9k3lZAjLTxjasVsGZttX7QChJJ4NNR6TKyxWFmrcPMJqeBPS4jez16yrxaQoJ4IWGS8wsz/qBJL/4/ePXqnismfN2LB5//0qQXz5VlfRC1Nkiq3k8ng5fOJjf9LS4GWFz0NjuJNrnDg4D4jE8LAS2EFPPi52WBpMtDnTAPyfC+lLV2ZWOdv3Y0D9oJfxSQ88ekECw7D9l5IbKnr/CLhW1obXjm1nvDs3hAS4XDwk+1VpbURLHKZmGL00ilRw9+QUY5bMprgkiqEDpJRi241XjXObxylyW8h5YH6vBDfIsmSJLRS1+Li+FRTkZG2xgVbSPK4gK1Pzz7+8LLCaQgh45TFb0addJbIH0gZa2qasTdbUcToZ3wDYCcN2QgoaqrCbkE2Y1hB5gGVBLovKALgFfP7toovq6MZWF1NMtqLVS7DBCUwuTWBtCpQ2jrTPGWwEG/v1+W8ItBQBBbrO/VIVLMbkZHO5gUV6M8OkTbw8fm0yjHFjb9veEtSMYa1MnvIBlflrJWbWmxA2rHX6Kd8PWAnD9qPMGSGwhVnxae5US4SxM21w1ehSx5NdHMLY9nXnksy2qiCAofnXCa6fwYNEHx7iMKrLUkAjJ4A2G/ArIavdHLcTE2piVVcVpiFSnRteFjchvC637EUsUHkljCxMxCk/aElLlsVUsfRzt+j3bCHwHk/FETCJbeSrBiUvjmNoa963pPeDZ3mplbmsC7JYl8VRmD260HdQD0Pswq+deRs1aEgxaAS8z+gvxBDVaTh6mJ1ZyXXMHJSRVgcoJXFzb5ZXGUnrBzUp3wCZqsB6SM71a39HG042e0E/5PIOcNGITsvotAyWlhx5UhHBc3ukEtU1gdwxtFKbxbnMjOGkuY1gYvZnWo1ZL8L8kfUIHXoLzWJ9bGRWnl/C2tlPiYWhB/E7O+QnyR+KcHlf591On3Slmrt7f0MbSjnfCHhVwwJplg9f8RyL8yTHQxo0tgcin/bylP4Pn8VN4uTsTp0iuebYPe3yrM9cYiv1jQeMVyxa8jzuLm4tQyrskqpmN8VfiUu... [truncated]';
        });
        const aspect = logoTex.image.width / logoTex.image.height;
        const logoH = 0.62; const logoW = logoH * aspect;
        const logo = new TEX.Mesh(
          new TEX.PlaneGeometry(logoW, logoH),
          new TEX.MeshBasicMaterial({ map: logoTex, transparent: true, depthWrite: false })
        );
        logo.position.set(0, 0.0, 0.07); card.add(logo);

        const makeText = (text, { weight = 300, px = 110, color = '#2b2b2f', planeW = 2.6, align = 'center' } = {}) => {
          const c = document.createElement('canvas');
          const ctx = c.getContext('2d');
          const font = `${weight} ${px}px "Cormorant Garamond", Georgia, "Times New Roman", serif`;
          ctx.font = font;
          const tw = Math.ceil(ctx.measureText(text).width);
          c.width = tw + 40; c.height = px + 40;
          const x = c.getContext('2d');
          x.font = font; x.fillStyle = color; x.textBaseline = 'middle';
          x.textAlign = align === 'right' ? 'right' : align === 'left' ? 'left' : 'center';
          x.fillText(text, align === 'right' ? c.width - 20 : align === 'left' ? 20 : c.width / 2, c.height / 2);
          const t = new TEX.CanvasTexture(c); t.colorSpace = TEX.SRGBColorSpace; t.anisotropy = 8;
          const ph = planeW * (c.height / c.width);
          return new TEX.Mesh(new TEX.PlaneGeometry(planeW, ph), new TEX.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
        };

        const brand = makeText('ELIZABETH SETON', { weight: 300, px: 104, planeW: 2.6 });
        brand.position.set(0, 0.66, 0.07); card.add(brand);
        const name = makeText('J ADRIATICO', { weight: 300, px: 82, planeW: 1.4, align: 'left' });
        name.position.set(-0.62, -0.74, 0.07); card.add(name);

        const mc = document.createElement('canvas'); mc.width = 720; mc.height = 260;
        const mctx = mc.getContext('2d');
        mctx.fillStyle = '#2b2b2f'; mctx.textAlign = 'right'; mctx.textBaseline = 'alphabetic';
        mctx.font = '300 46px "Cormorant Garamond", Georgia, serif';
        mctx.fillText('MEMBER SINCE', 700, 120);
        mctx.font = '300 116px "Cormorant Garamond", Georgia, serif';
        mctx.fillText('22', 700, 236);
        const mtex = new TEX.CanvasTexture(mc); mtex.colorSpace = TEX.SRGBColorSpace; mtex.anisotropy = 8;
        const member = new TEX.Mesh(new TEX.PlaneGeometry(1.3, 1.3 * (260 / 720)),
          new TEX.MeshBasicMaterial({ map: mtex, transparent: true, depthWrite: false }));
        member.position.set(0.78, -0.68, 0.07); card.add(member);

        const chipC = document.createElement('canvas'); chipC.width = chipC.height = 256;
        const chipx = chipC.getContext('2d');
        chipx.fillStyle = '#e8cd8a'; chipx.strokeStyle = '#a98a32'; chipx.lineWidth = 10;
        chipx.fillRect(40, 70, 176, 116); chipx.strokeRect(40, 70, 176, 116);
        chipx.beginPath(); chipx.moveTo(128, 70); chipx.lineTo(128, 186); chipx.moveTo(40, 128); chipx.lineTo(216, 128); chipx.stroke();
        chipx.strokeRect(72, 102, 40, 52); chipx.strokeRect(144, 102, 40, 52);
        const chipTex = new TEX.CanvasTexture(chipC); chipTex.colorSpace = TEX.SRGBColorSpace; chipTex.anisotropy = 8;
        const chip = new TEX.Mesh(new TEX.PlaneGeometry(0.4, 0.4), new TEX.MeshBasicMaterial({ map: chipTex, transparent: true, depthWrite: false }));
        chip.position.set(-1.12, 0.28, 0.07); card.add(chip);

        const cc = document.createElement('canvas'); cc.width = cc.height = 256;
        const cx3 = cc.getContext('2d'); cx3.strokeStyle = '#7c5a1e'; cx3.lineWidth = 16; cx3.lineCap = 'round';
        for (let i = 1; i <= 3; i++) { cx3.beginPath(); cx3.arc(70, 128, 26 * i, -Math.PI / 2.6, Math.PI / 2.6); cx3.stroke(); }
        const ctex = new TEX.CanvasTexture(cc); ctex.colorSpace = TEX.SRGBColorSpace; ctex.anisotropy = 8;
        const contactless = new TEX.Mesh(new TEX.PlaneGeometry(0.34, 0.34), new TEX.MeshBasicMaterial({ map: ctex, transparent: true, depthWrite: false }));
        contactless.position.set(1.12, 0.28, 0.07); card.add(contactless);
      } catch (e) { console.warn('logo not loaded', e); }

      // ---- soft reflection + contact shadow under the card ----
      const reflCanvas = (() => {
        const c = document.createElement('canvas'); c.width = 1024; c.height = 320;
        const x = c.getContext('2d');
        const g = x.createLinearGradient(0, 0, 0, 320);
        g.addColorStop(0, 'rgba(231,200,132,0.55)'); g.addColorStop(1, 'rgba(231,200,132,0)');
        // fade sides
        x.fillStyle = g; x.fillRect(0, 0, 1024, 320);
        const fade = x.createLinearGradient(0, 0, 1024, 0);
        fade.addColorStop(0, 'rgba(0,0,0,1)'); fade.addColorStop(0.25, 'rgba(0,0,0,0)');
        fade.addColorStop(0.75, 'rgba(0,0,0,0)'); fade.addColorStop(1, 'rgba(0,0,0,1)');
        x.globalCompositeOperation = 'destination-out'; x.fillStyle = fade; x.fillRect(0, 0, 1024, 320);
        const t = new TEX.CanvasTexture(c); t.colorSpace = TEX.SRGBColorSpace; return t;
      })();
      const reflection = new TEX.Mesh(
        new TEX.PlaneGeometry(3.0, 1.5),
        new TEX.MeshBasicMaterial({ map: reflCanvas, transparent: true, depthWrite: false, opacity: 0.5, rotation: Math.PI })
      );
      reflection.position.y = -1.12; reflection.scale.y = -1; scene.add(reflection);

      const sc = document.createElement('canvas'); sc.width = sc.height = 256;
      const sx = sc.getContext('2d');
      const rg = sx.createRadialGradient(128, 128, 8, 128, 128, 128);
      rg.addColorStop(0, 'rgba(0,0,0,0.45)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
      sx.fillStyle = rg; sx.fillRect(0, 0, 256, 256);
      const shadow = new TEX.Mesh(new TEX.PlaneGeometry(3.2, 1.8),
        new TEX.MeshBasicMaterial({ map: new TEX.CanvasTexture(sc), transparent: true, depthWrite: false, opacity: 0.8 }));
      shadow.rotation.x = -Math.PI / 2; shadow.position.y = -1.2; scene.add(shadow);

      // ---- interaction: drag-orbit + click ripple ----
      const clock = new TEX.Clock();
      let targetRX = -0.06, targetRY = 0.0, curRX = -0.06, curRY = 0.0;
      let autoSpin = true, dragging = false, lastX = 0, lastY = 0, idleT = 0, t0 = performance.now();
      const ripples = [];
      const hint = document.getElementById('stageHint');

      function ripple(clientX, clientY) {
        const rect = canvas.getBoundingClientRect();
        const nx = ((clientX - rect.left) / rect.width) * 2 - 1;
        const ny = -(((clientY - rect.top) / rect.height) * 2 - 1);
        const geoR = new TEX.RingGeometry(0.02, 0.05, 48);
        const matR = new TEX.MeshBasicMaterial({ color: 0xfff4d8, transparent: true, opacity: 0.9, side: TEX.DoubleSide, depthWrite: false });
        const ring = new TEX.Mesh(geoR, matR);
        ring.position.set(nx * 1.7, ny * 1.05, 0.12);
        ring.lookAt(camera.position);
        scene.add(ring);
        ripples.push({ ring, mat: matR, born: clock.getElapsedTime() });
      }

      canvas.addEventListener('pointerdown', (e) => {
        dragging = true; autoSpin = false; lastX = e.clientX; lastY = e.clientY;
        canvas.setPointerCapture(e.pointerId);
        if (hint) hint.classList.add('hide');
      });
      canvas.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const dx = e.clientX - lastX, dy = e.clientY - lastY;
        lastX = e.clientX; lastY = e.clientY;
        targetRY += dx * 0.008;
        targetRX += dy * 0.006;
        targetRX = Math.max(-1.1, Math.min(1.1, targetRX));
        idleT = 0;
      });
      const endDrag = (e) => {
        if (!dragging) return;
        dragging = false;
        const moved = Math.abs(e.clientX - lastX) + Math.abs(e.clientY - lastY); // ignored; click handled below
        // resume auto-spin after a pause
        clearTimeout(endDrag._t);
        endDrag._t = setTimeout(() => { autoSpin = true; }, 2600);
      };
      canvas.addEventListener('pointerup', (e) => {
        const wasDrag = Math.abs(e.clientX - lastDownX) + Math.abs(e.clientY - lastDownY) > 6;
        dragging = false;
        if (!wasDrag) ripple(e.clientX, e.clientY);
        clearTimeout(endDrag._t);
        endDrag._t = setTimeout(() => { autoSpin = true; }, 2600);
      });
      canvas.addEventListener('pointercancel', endDrag);
      let lastDownX = 0, lastDownY = 0;
      canvas.addEventListener('pointerdown', (e) => { lastDownX = e.clientX; lastDownY = e.clientY; });

      const render = () => {
        if (!reduced) requestAnimationFrame(render);
        const t = clock.getElapsedTime();
        if (autoSpin && !dragging) {
          // cinematic 360° idle drift, like a hero item
          targetRY += 0.006;
          targetRX = -0.06 + Math.sin(t * 0.3) * 0.05;
        }
        curRY += (targetRY - curRY) * 0.08;
        curRX += (targetRX - curRX) * 0.08;
        card.rotation.y = curRY;
        card.rotation.x = curRX;
        card.position.y = Math.sin(t * 0.8) * 0.05;
        reflection.position.y = -1.12 + Math.sin(t * 0.8) * 0.05 * -1;
        reflection.visible = card.position.y > -0.02;
        // ripples
        for (let i = ripples.length - 1; i >= 0; i--) {
          const rp = ripples[i]; const age = t - rp.born;
          const s = 1 + age * 9;
          rp.ring.scale.set(s, s, s);
          rp.mat.opacity = Math.max(0, 0.9 - age * 1.1);
          if (rp.mat.opacity <= 0) { scene.remove(rp.ring); rp.ring.geometry.dispose(); rp.mat.dispose(); ripples.splice(i, 1); }
        }
        renderer.render(scene, camera);
      };
      render();

      window.addEventListener('resize', () => {
        const wpx = canvas.clientWidth, hpx = canvas.clientHeight;
        camera.aspect = wpx / hpx; camera.updateProjectionMatrix();
        renderer.setSize(wpx, hpx, false);
      });
    } catch (err) {
      console.warn('Three.js card disabled:', err);
    }
  })();
