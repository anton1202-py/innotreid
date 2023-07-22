$(function () {
   
    $('.sidebar').each(function () {
        var link = $(this).find('a').attr('href');
 
        if (cur_url == link) {
            $(this).addClass('active');
        }
        return alert( location );
    });
});
