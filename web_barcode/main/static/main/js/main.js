let xhttp = new XMLHttpRequest();

// ========== Обрабатывает нажати кнопки загрузить из файла ========= //
function submitForm() {
  document.getElementById('uploadForm').submit();
}


//  =========== ВЫДЕЛЕНИЕ  ЗЕЛЕНЫМ ЦВЕТОМ ВЫПОЛНЕННОГО ОБЪЕМА ПРОИЗВОДСТВА =========
const elements = document.getElementsByTagName("th");
const values = document.getElementsByTagName("td");
const table = document.querySelector('table.production_delivery_data')

var amount_table = document.querySelectorAll('td:nth-of-type(4)');
// console.log(amount_table)
// for (i in amount_table) {
//   console.log(i)
//}

var produced_table = document.querySelectorAll('td:nth-of-type(5)');

if (elements && values && table) {
  var rows = table.getElementsByTagName('tr')
  for (var element = 0; element < amount_table.length; ++element) {
    // console.log(amount_table.length)
    // console.log(table_fill.length)
    // console.log(cells)
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

const tableDeliveryNumber = document.querySelector('table.delivery_number')
var deliveryCol = document.querySelectorAll('td#progress-col');

if (tableDeliveryNumber && deliveryCol) {
  var taskRows = tableDeliveryNumber.getElementsByTagName('tr')
  for (var elem = 0; elem < deliveryCol.length; ++elem) {
    if (deliveryCol[elem].textContent == '100%') {
      taskRows[elem+2].style.background = '#eaffe8';
    } else if (deliveryCol[elem].textContent == '0%') {
      taskRows[elem+2].style.background = '#ffe8e8';
    } else {
      taskRows[elem+2].style.background = '#ffffe8';
    }
  }
     } else {
  console.error('Элементы th, td и table не найдены на странице');
}
// =========== При нажатии на чек бокс меняется цвет ячейки ==========
// function changeColor(checkbox) {
//   var cell = checkbox.parentNode.parentNode;
//   if (checkbox.checked) {
//     cell.style.backgroundColor = "#c2ffbd";
//   } else {
//     cell.style.backgroundColor = "white";
//   }
// }

// =========== При нажатии на чек бокс меняется цвет ячейки с датой ==========
// function changeDateColor(checkbox) {
//   var dateCell = checkbox.parentNode.parentNode.nextElementSibling;
//   if (checkbox.checked) {
//     dateCell.style.backgroundColor = "green";
//   } else {
//     dateCell.style.backgroundColor = "";
//   }
//}