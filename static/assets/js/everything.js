document.addEventListener('DOMContentLoaded', function() {
    // Sidebar functionality
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');
    const logo = document.querySelector('.logo'); // Logo element
    const middleColumn = document.querySelector('.main-header .col-4:nth-child(2)'); // Middle header section
    const logoHeader = document.querySelector('.logo-header'); // Sidebar logo header

    // Function to update the logo position based on sidebar state and screen width
    function updateLogoPosition() {
        if (window.innerWidth <= 467) {
            if (sidebar.classList.contains('expanded')) {
                // Move menu toggle button back to sidebar when sidebar is expanded on small screens
                sidebar.prepend(menuToggle);
            } else {
                // Keep both logo and menu toggle in the main header when collapsed
                middleColumn.appendChild(logo);
                middleColumn.appendChild(menuToggle);
            }
        } else if (sidebar.classList.contains('collapsed')) {
            // For larger screens, move logo to main header only when collapsed
            middleColumn.appendChild(logo);
            sidebar.prepend(menuToggle);
        } else {
            // For larger screens and expanded sidebar, keep logo in the sidebar
            logoHeader.prepend(logo);
            sidebar.prepend(menuToggle);
        }
    }

    // Initial setup based on screen width
    function initializeSidebarState() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            sidebar.classList.remove('expanded');
        }
        updateLogoPosition();
    }

    // Run initial setup on load
    initializeSidebarState();

    // Toggle sidebar and update logo position on button click
    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        sidebar.classList.toggle('expanded');
        updateLogoPosition(); // Adjust logo position after toggling
    });

    // Handle window resize to adjust sidebar state and logo position
    window.addEventListener('resize', function() {
        initializeSidebarState(); // Re-run initialization on resize
    });

    // Card functionality
    const cards = document.querySelectorAll('.card');

    // Add hover and active effects
    cards.forEach(card => {
        // Hover effect
        card.addEventListener('mouseenter', () => {
            card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
            card.style.transform = 'translateY(-5px)'; // Lifts the card slightly
            card.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.3)'; // Stronger shadow on hover
        });

        // Remove hover effect
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.15)'; // Reset to default shadow
        });

        // Active (click) effect
        card.addEventListener('mousedown', () => {
            card.style.transition = 'transform 0.1s ease, box-shadow 0.1s ease';
            card.style.transform = 'translateY(-2px)'; // Less lift on click
            card.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.35)'; // Stronger shadow when active
        });

        // Reset after click
        card.addEventListener('mouseup', () => {
            card.style.transform = 'translateY(-5px)'; // Return to hover state lift
            card.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.3)'; // Return to hover shadow
        });
    });

    // Datepicker functionality
    function initializeDatepicker(inputId, calendarId) {
        const dateInput = document.getElementById(inputId);
        const calendar = document.getElementById(calendarId);
        const monthDisplay = calendar.querySelector(".month");
        const prevButton = calendar.querySelector(".prev-month");
        const nextButton = calendar.querySelector(".next-month");
        const calendarDays = calendar.querySelector(".calendar-days");
        let currentDate = new Date();
        let currentMonth = currentDate.getMonth();
        let currentYear = currentDate.getFullYear();

        // Function to render the calendar based on the current month and year
        function renderCalendar() {
            monthDisplay.textContent = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
            calendarDays.innerHTML = `
                <div class="day">Sun</div>
                <div class="day">Mon</div>
                <div class="day">Tue</div>
                <div class="day">Wed</div>
                <div class="day">Thu</div>
                <div class="day">Fri</div>
                <div class="day">Sat</div>
            `;

            const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
            const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);
            const daysInMonth = lastDayOfMonth.getDate();
            const firstDay = firstDayOfMonth.getDay();

            // Create empty divs for the days before the start of the month
            for (let i = 0; i < firstDay; i++) {
                calendarDays.innerHTML += '<div class="day-number empty"></div>';
            }

            // Create divs for each day of the month
            for (let day = 1; day <= daysInMonth; day++) {
                calendarDays.innerHTML += `<div class="day-number">${day}</div>`;
            }

            // Add click event for each day number to set the value in the input field
            const dayNumbers = calendar.querySelectorAll(".day-number:not(.empty)");
            dayNumbers.forEach((day) => {
                day.addEventListener("click", function() {
                    // Format the date as YYYY-MM-DD
                    const dayValue = day.textContent.padStart(2, '0');
                    dateInput.value = `${currentYear}-${(currentMonth + 1).toString().padStart(2, '0')}-${dayValue}`;
                    calendar.style.display = "none";  // Hide the calendar after selecting a date
                });
            });
        }

        // Event listener for the "previous month" button
        prevButton.addEventListener("click", () => {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            currentDate = new Date(currentYear, currentMonth, 1);
            renderCalendar();
        });

        // Event listener for the "next month" button
        nextButton.addEventListener("click", () => {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            currentDate = new Date(currentYear, currentMonth, 1);
            renderCalendar();
        });

        // Toggle calendar visibility when the input field is clicked
        dateInput.addEventListener("click", () => {
            calendar.style.display = calendar.style.display === "block" ? "none" : "block";
        });

        // Hide the calendar if the user clicks outside
        document.addEventListener("click", (e) => {
            if (!calendar.contains(e.target) && e.target !== dateInput) {
                calendar.style.display = "none";
            }
        });

        // Initial render of the calendar
        renderCalendar();
    }

    // Initialize the custom datepickers for all inputs with class 'custom-date-input'
    const datepickers = document.querySelectorAll('.custom-date-input');
    datepickers.forEach((input) => {
        const calendarId = input.getAttribute('data-calendar-id');
        initializeDatepicker(input.id, calendarId);
    });
});
