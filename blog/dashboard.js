// dashboard.js


// Additional functions in dashboard.js

// Function to add a widget
function addWidget(widgetType) {
  // Logic to add a widget to the dashboard
}

// Function to remove a widget
function removeWidget(widgetId) {
  // Logic to remove a widget from the dashboard
}

// Event listeners for widget interaction
document.querySelectorAll('.add-widget-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    addWidget(this.dataset.widgetType);
  });
});

document.querySelectorAll('.remove-widget-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    removeWidget(this.dataset.widgetId);
  });
});

// Implement drag-and-drop functionality with a library like SortableJS or with native HTML5 drag-and-drop

document.addEventListener('DOMContentLoaded', function() {
  // Function to load wallet data
  function loadWalletData() {
    // Replace with the correct URL that will return wallet data
    fetch('/path/to/wallet/data/')
      .then(response => response.json())
      .then(data => {
        // Populate the wallet info div with data
        const walletInfoDiv = document.getElementById('wallet-info');
        walletInfoDiv.innerHTML = `
          <p>Wallet Address: ${data.wallet_address}</p>
          <p>Balance: ${data.balance}</p>
          // Add more wallet data as needed
        `;
      });
  }

  // Call the loadWalletData function on page load
  loadWalletData();
});
