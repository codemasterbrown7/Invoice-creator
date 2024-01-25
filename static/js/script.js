document.addEventListener('DOMContentLoaded', function() {
    var createInvoiceBtn = document.getElementById('create-invoice');
    if (createInvoiceBtn) {
        createInvoiceBtn.addEventListener('click', function() {
            window.location.href = '/create-invoice'; // Redirect to the invoice creation page
        });
    }

    var addAddressBtn = document.getElementById('addAddressBtn');
    if (addAddressBtn) {
        addAddressBtn.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent form submission
            addAddressField(); // Call function to add new address fields
        });
    }
});

// Function to dynamically add address fields
function addAddressField() {
    var addressInputs = document.getElementById('addressInputs');

    var newInputGroup = document.createElement('div');
    newInputGroup.className = 'input-group mb-2';

    // Create the 'from' address input
    var fromInput = document.createElement('input');
    fromInput.type = 'text';
    fromInput.name = 'addresses[]';
    fromInput.placeholder = 'From Address';
    fromInput.className = 'form-control';

    // Create the 'to' address input
    var toInput = document.createElement('input');
    toInput.type = 'text';
    toInput.name = 'addresses[]';
    toInput.placeholder = 'To Address';
    toInput.className = 'form-control';

    newInputGroup.appendChild(fromInput);
    newInputGroup.appendChild(toInput);
    
    addressInputs.appendChild(newInputGroup);
}


function updateReportHours() {
    var contactHours = parseFloat(document.getElementById('supervisedContactHours').value) || 0;
    var clientLate = document.getElementById('clientLate').checked;
    var maxReportHours = (contactHours <= 1) ? 0.5 : 1;

    if (clientLate) {
        maxReportHours = 0.25; // 15 minutes
    }

    document.getElementById('contactReportHours').max = maxReportHours;
}

document.getElementById('supervisedContactHours').addEventListener('change', updateReportHours);
document.getElementById('clientLate').addEventListener('change', updateReportHours);

// Call it initially to set the proper state
updateReportHours();
