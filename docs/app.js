async function loadProducts(){
  try{
    const res = await fetch('data/products.json?cache=' + Date.now());
    const data = await res.json();
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    (data.products || []).forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      const img = document.createElement('img');
      img.src = p.image_url || '';
      img.alt = p.title || '';
      const pad = document.createElement('div');
      pad.className = 'pad';
      const h3 = document.createElement('h3');
      h3.textContent = p.title || '';
      const price = document.createElement('div');
      price.className = 'price';
      const pr = (p.price !== undefined && p.currency) ? `${p.currency} ${p.price.toFixed(2)}` : '';
      price.textContent = pr;
      const a = document.createElement('a');
      a.className = 'btn';
      a.href = p.url || '#';
      a.target = '_blank';
      a.rel = 'nofollow sponsored noopener';
      a.textContent = 'View';
      pad.appendChild(h3);
      pad.appendChild(price);
      pad.appendChild(a);
      card.appendChild(img);
      card.appendChild(pad);
      grid.appendChild(card);
    });
    const updated = document.getElementById('updated_at');
    const ts = data.updated_at ? new Date(data.updated_at * 1000) : new Date();
    updated.textContent = ts.toLocaleString();
    document.getElementById('year').textContent = new Date().getFullYear();
  }catch(e){
    console.error(e);
  }
}
loadProducts();
