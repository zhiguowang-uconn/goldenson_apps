const fundInput = document.getElementById("retirementFund");
const fundHelp = document.getElementById("fundHelp");
const MAX_VALUE = 5000000;

fundInput.addEventListener("input", function (e) {
  // Remove commas
  let value = e.target.value.replace(/,/g, "");

  // Keep only digits
  value = value.replace(/\D/g, "");

  // Cap at MAX_VALUE
  if (value) {
    let num = parseInt(value, 10);
    if (num > MAX_VALUE) {
      num = MAX_VALUE;
      fundHelp.classList.remove("d-none"); // show warning
    } else {
      fundHelp.classList.add("d-none"); // hide warning
    }
    e.target.value = num.toLocaleString();
  } else {
    e.target.value = "";
    fundHelp.classList.add("d-none");
  }
});

// This is an example script, please modify as needed
const rangeInput = document.getElementById("age");
const rangeOutput = document.getElementById("ageRangeValue");

// Set initial value
rangeOutput.textContent = rangeInput.value;

rangeInput.addEventListener("input", function () {
  rangeOutput.textContent = this.value;
});

// Controls that maxsri must be greater than minsri
document.addEventListener("DOMContentLoaded", () => {
  const minInput = document.getElementById("minsri");
  const maxInput = document.getElementById("maxsri");
  const minError = document.getElementById("minsriError");
  const maxError = document.getElementById("maxsriError");
  const submitBtn = document.getElementById("submitBtn");

  function validateRanges() {
    const minVal = parseInt(minInput.value);
    const maxVal = parseInt(maxInput.value);

    let valid = true;

    // Validate minsri
    if (isNaN(minVal) || minVal < 0 || minVal > 100) {
      minError.style.display = "block";
      minInput.classList.add("is-invalid");
      valid = false;
    } else {
      minError.style.display = "none";
      minInput.classList.remove("is-invalid");
    }

    // Validate maxsri
    if (isNaN(maxVal) || maxVal < minVal || maxVal > 100) {
      maxError.style.display = "block";
      maxInput.classList.add("is-invalid");
      valid = false;
    } else {
      maxError.style.display = "none";
      maxInput.classList.remove("is-invalid");
    }

    // Enable/disable submit button
    submitBtn.disabled = !valid;
  }

  minInput.addEventListener("input", validateRanges);
  maxInput.addEventListener("input", validateRanges);

  // Run once at page load
  validateRanges();
});


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("sriForm");
    const resultDiv = document.getElementById("result");
  
    form.addEventListener("submit", function(e) {
      e.preventDefault();
  
      const formData = Object.fromEntries(new FormData(form));
  
      fetch("/sriresult", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(formData)
      })
      .then(res => res.json())
      .then(data => {
        resultDiv.innerHTML = data.html; // inject the rendered table

        // scroll to top smoothly
      window.scrollTo({ top: 0, behavior: "smooth" });
      })
      .catch(err => console.error(err));
    });
  });
