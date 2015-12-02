{%- extends 'full.tpl' -%}

{% block output_group %}
<div class="output_hidden">
{{ super() }}
</div>
{% endblock output_group %}

{% block input_group -%}
<div class="input_hidden">
{{ super() }}
</div>
{% endblock input_group %}

{%- block header -%}
{{ super() }}

<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>

<style type="text/css">

div.output_wrapper {
  margin-top: 0px;

}

div.input_wrapper {
  margin-top: 0px;
}

.input_hidden {
  display: none;
}


#show_all, #hide_all {
   border: 1px solid #ffffff;
   background: #ffffff;
   background: -webkit-gradient(linear, left top, left bottom, from(#ffffff), to(#ffffff));
   background: -webkit-linear-gradient(top, #ffffff, #ffffff);
   background: -moz-linear-gradient(top, #ffffff, #ffffff);
   background: -ms-linear-gradient(top, #ffffff, #ffffff);
   background: -o-linear-gradient(top, #ffffff, #ffffff);
   padding: 2px 4px;
   -webkit-border-radius: 0px;
   -moz-border-radius: 0px;
   border-radius: 0px;
   -webkit-box-shadow: rgba(0,0,0,0) 0 0px 0;
   -moz-box-shadow: rgba(0,0,0,0) 0 0px 0;
   box-shadow: rgba(0,0,0,0) 0 0px 0;
   text-shadow: rgba(0,0,0,0) 0 0px 0;
   color: #000000;
   //font-size: 10px;
   font-family: Century Gothic, Arial, Sans-Serif;
   text-decoration: none;
   vertical-align: middle;
   }
#show_all:hover, #hide_all:hover {
   border-top-color: #ffffff;
   background: #ffffff;
   color: #cc0000;
   }
#show_all:active, #hide_all:active {
   border-top-color: #ffffff;
   background: #ffffff;
   }


</style>

<script>
$(document).ready(function(){
        
    $("#notebook-container").prepend("<button id='show_all'>Show All</button><button id='hide_all'>Hide All</button>")

    $(".output_hidden").click(function(){
      $(this).prev('.input_hidden').slideToggle();
    });
                           
    $(".inner_cell").click(function(){
      $(this).next('.input_hidden').slideToggle();
    });
                           
    $(".input_hidden").click(function(){
      $(this).slideToggle();
    });

    $('.inner_cell').click(function(){
        var element = $(this).parent().next().children('div:first');
        if (element.attr('class') == 'input_hidden'){
            if (element.is(':visible')){
                element.slideUp();
                }
            else{
                element.slideDown();
            }
        }
    });
        
    $("#show_all").click(function(){
      $('.input_hidden').slideDown();
    });
        
    $("#hide_all").click(function(){
      $('.input_hidden').slideUp();
    }); 
});
</script>
        
<style>

</style>

{%- endblock header -%}