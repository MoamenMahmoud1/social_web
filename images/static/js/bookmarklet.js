const siteUrl = 'https://mysite.com:8001/';
const minWidth = 250;
const minHeight = 250;

// load CSS dynamically
(function loadCSS() {
  const head = document.getElementsByTagName('head')[0];
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.type = 'text/css';
  link.href = siteUrl + 'static/css/bookmarklet.css?r=' + Math.random();
  head.appendChild(link);
})();

// load HTML dynamically
(function loadHTML() {
  const body = document.getElementsByTagName('body')[0];
  const boxHtml = `
    <div id="bookmarklet" style="display:none">
      <a href="#" id="close">&times;</a>
      <h1>Select an image to bookmark:</h1>
      <div class="images"></div>
    </div>`;
  body.insertAdjacentHTML('beforeend', boxHtml);
})();

function bookmarkletLaunch() {
  const bookmarklet = document.getElementById('bookmarklet');
  const imagesFound = bookmarklet.querySelector('.images');

  // clear
  imagesFound.innerHTML = '';

  // show box
  bookmarklet.style.display = 'block';

  // close button
  bookmarklet.querySelector('#close')
    .addEventListener('click', function(e){
      e.preventDefault();
      bookmarklet.style.display = 'none';
    });

  // get all images
  const images = document.querySelectorAll('img');
  images.forEach(image => {
    if (image.naturalWidth >= minWidth && image.naturalHeight >= minHeight) {
      const imageFound = document.createElement('img');
      imageFound.src = image.src;
      imagesFound.append(imageFound);
    }
  });

  // click event
  imagesFound.querySelectorAll('img').forEach(image => {
    image.addEventListener('click', function(event){
      const imageSelected = event.target;
      bookmarklet.style.display = 'none';
      window.open(siteUrl + 'images/create/?url=' + 
        encodeURIComponent(imageSelected.src) + 
        '&title=' + encodeURIComponent(document.title),
        '_blank');
    });
  });
}

// launch
bookmarkletLaunch();
