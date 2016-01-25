<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>reveal.js - The HTML Presentation Framework</title>
  <link rel="stylesheet" href="{{ cdn }}/{{ version }}/css/reveal.min.css">
  <link rel="stylesheet" href="{{ cdn }}/{{ version }}/css/theme/default.css" id="theme">
</head>
<body>

  <!-- Slides  content to be added here -->
  <div class='reveal'>
    <div class='slides'>
        {% for slide in presentation %}
        <section>
        {{ slide }}
        </section>
        {% endfor %}
    </div>
  </div>

  <script src="{{ cdn }}/{{ version }}/lib/js/head.min.js"></script>
  <script src="{{ cdn }}/{{ version }}/js/reveal.js"></script>
  <script>
    // Full list of configuration options available here:
    // https://github.com/hakimel/reveal.js#configuration
    Reveal.initialize({
      controls: true,
      progress: true,
      history: true,
      center: true,
    });
  </script>
</body>
</html>