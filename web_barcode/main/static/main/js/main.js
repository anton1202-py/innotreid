let xhttp = new XMLHttpRequest();

// xhttp.onreadystatechange = function () {
//     if (this.readyState == 4 && this.status == 200) {
//         myFunction(this.responseText)
//     }
// }

// xhttp.open("GET", "/production/delivery_number", true)
// xhttp.send();


// function myFunction(data) {
//     console.log(data);
// }


// let xhttp2 = new XMLHttpRequest();
// xhttp2.onreadystatechange = function() {
//     if (this.readyState == 4 && this.status == 200) {
//         myFunction2(this.responseText)
//     }
// }

// xhttp2.open("POST", "/production/delivery_number", true)
// xhttp2.setRequestHeader('Content-type', 'application/x-www-form-urlencoded')
// //xhttp2.setRequestHeader('Authorization', 'Basic ' + authorizationBasic);
// xhttp2.setRequestHeader('Accept', 'application/json');
// xhttp2.setRequestHeader('X-CSRFToken', csrftoken);
// xhttp2.send("username=admin&password=admin&grant_type=password");


// function myFunction2(data) {
//     console.log(data);
// }


// const csrftoken = 'VeH9eLwlCXnmrPAj2JmMy7wCKKwYdKDgHq6yXOkf2al6YDcGTtoewNTvQFn1vxto';
// console.log(csrftoken)

// const xhttp2 = new XMLHttpRequest();
// xhttp2.onreadystatechange = function() {
//   if (this.readyState == 4 && this.status == 200) {
//     console.log(this.responseText);
//   }
// };

// const formData = new FormData();
// formData.append('username', 'admin');
// formData.append('password', 'admin');
// formData.append('csrfmiddlewaretoken', csrftoken);

// xhttp2.open("POST", "/production/delivery_number", true);
// xhttp2.send(formData);


//  =========== ВЫДЕЛЕНИЕ  ЗЕЛЕНЫМ ЦВЕТОМ ВЫПОЛНЕННОГО ОБЪЕМА ПРОИЗВОДСТВА =========
const elements = document.getElementsByTagName("th");
const values = document.getElementsByTagName("td");
const table = document.querySelector('table.production_delivery_data')
console.log(table);
var rows = table.getElementsByTagName('tr')

for (var i = 0; i < rows.length; i++) {
  var cells = rows[i].getElementsByTagName("td");
  var cell_value = cells[4]; // получаем значение ячейки в пятом столбце
  console.log(cell_value);
}
var amount_table = document.querySelectorAll('td:nth-of-type(4)');
// console.log(amount_table)
// for (i in amount_table) {
//   console.log(i)
//}

var produced_table = document.querySelectorAll('td:nth-of-type(5)');

if (elements && values && table) {
  console.log(amount_table.length)
  for (var element = 0; element < amount_table.length; ++element) {
    
    if (Number(produced_table[element].textContent) >= Number(amount_table[element].textContent)) {
      // console.log(amount_table[element].textContent)
      // console.log(element)
      // console.log(produced_table[element].textContent)
      table.rows[element+2].style.background = '#eaffe8';
          } else if (Number(produced_table[element].textContent) > 0 && Number(produced_table[element].textContent) < Number(amount_table[element].textContent)) {
      table.rows[element+2].style.background = '#ffffe8';
          } else if (Number(produced_table[element].textContent) == 0) {
            table.rows[element+2].style.background = '#ffe8e8';
                }}
      } else {
  console.error('Элементы th, td и table не найдены на странице');
}
