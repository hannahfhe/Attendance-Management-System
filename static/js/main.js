let selectedDepartmentValue = '';
let selectedDepartmentUrl = '';

document.addEventListener('DOMContentLoaded', function() {
    initializeDepartmentDropdown();
});

function initializeDepartmentDropdown() {
    const dropdownBtn = document.getElementById('department-dropdown-btn');
    const dropdownMenu = document.getElementById('department-dropdown-menu');
    const dropdownArrow = document.getElementById('dropdown-arrow');
    const searchInput = document.getElementById('department-search');
    const departmentOptions = document.querySelectorAll('.department-option');
    const hiddenInput = document.getElementById('department-filter');

    // Toggle dropdown
    dropdownBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleDropdown();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!dropdownMenu.contains(e.target) && !dropdownBtn.contains(e.target)) {
            closeDropdown();
        }
    });

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterDepartmentOptions(this.value);
        });
    }

    // Department option selection
    departmentOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.stopPropagation();
            selectDepartment(this);
        });
        
        // Add keyboard navigation
        option.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectDepartment(this);
            }
        });
    });

    // Keyboard navigation for dropdown
    dropdownBtn.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleDropdown();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            openDropdown();
            focusFirstOption();
        }
    });
}

function toggleDropdown() {
    const dropdownMenu = document.getElementById('department-dropdown-menu');
    const dropdownArrow = document.getElementById('dropdown-arrow');
    
    if (dropdownMenu.classList.contains('hidden')) {
        openDropdown();
    } else {
        closeDropdown();
    }
}

function openDropdown() {
    const dropdownMenu = document.getElementById('department-dropdown-menu');
    const dropdownArrow = document.getElementById('dropdown-arrow');
    const searchInput = document.getElementById('department-search');
    
    dropdownMenu.classList.remove('hidden');
    dropdownArrow.style.transform = 'rotate(180deg)';
    
    // Focus search input
    if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
    }
}

function closeDropdown() {
    const dropdownMenu = document.getElementById('department-dropdown-menu');
    const dropdownArrow = document.getElementById('dropdown-arrow');
    const searchInput = document.getElementById('department-search');
    
    dropdownMenu.classList.add('hidden');
    dropdownArrow.style.transform = 'rotate(0deg)';
    
    // Clear search
    if (searchInput) {
        searchInput.value = '';
        filterDepartmentOptions('');
    }
}

function selectDepartment(option) {
    const value = option.dataset.value;
    const label = option.dataset.label;
    const url = option.dataset.url;
    
    selectedDepartmentValue = value;
    selectedDepartmentUrl = url || '';
    
    // Update display
    document.getElementById('selected-department').textContent = label;
    document.getElementById('department-filter').value = value;
    
    // Update visual selection
    document.querySelectorAll('.department-option').forEach(opt => {
        opt.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
    });
    
    option.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
    
    closeDropdown();
    
    // Trigger change event for compatibility with existing code
    const changeEvent = new Event('change', { bubbles: true });
    document.getElementById('department-filter').dispatchEvent(changeEvent);
}

function filterDepartmentOptions(searchTerm) {
    const options = document.querySelectorAll('.department-option');
    const lowerSearchTerm = searchTerm.toLowerCase();
    
    options.forEach(option => {
        const label = option.dataset.label.toLowerCase();
        const value = option.dataset.value.toLowerCase();
        
        if (label.includes(lowerSearchTerm) || value.includes(lowerSearchTerm)) {
            option.style.display = 'flex';
        } else {
            option.style.display = 'none';
        }
    });
}

function filterByDepartment() {
    closeDropdown();
    
    // Call your existing filter function
    if (typeof applyFilters === 'function') {
        applyFilters();
    } else {
        // Fallback to manual filtering
        console.log('Filtering by department:', selectedDepartmentValue);
    }
}

function viewDepartmentDetails() {
    if (selectedDepartmentUrl) {
        window.location.href = selectedDepartmentUrl;
    } else {
        alert('No dedicated page available for this department.');
    }
}

function focusFirstOption() {
    const firstOption = document.querySelector('.department-option:not([style*="display: none"])');
    if (firstOption) {
        firstOption.focus();
    }
}

// Helper function to set department programmatically
function setDepartment(value, label) {
    selectedDepartmentValue = value;
    document.getElementById('selected-department').textContent = label || value || 'All Departments';
    document.getElementById('department-filter').value = value;
    
    // Update visual selection
    document.querySelectorAll('.department-option').forEach(opt => {
        opt.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
        if (opt.dataset.value === value) {
            opt.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
        }
    });
}

 document.addEventListener('DOMContentLoaded', function() {
            // Mobile menu toggle functionality
            const mobileMenuButton = document.getElementById('mobile-menu-button');
            const mobileMenu = document.getElementById('mobile-menu');
            const menuIcon = document.getElementById('menu-icon');
            const closeIcon = document.getElementById('close-icon');

            // Check if elements exist before adding event listeners
            if (mobileMenuButton && mobileMenu && menuIcon && closeIcon) {
                mobileMenuButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log('Mobile menu button clicked'); // Debug log
                    
                    const isHidden = mobileMenu.classList.contains('hidden');
                    
                    if (isHidden) {
                        mobileMenu.classList.remove('hidden');
                        menuIcon.classList.add('hidden');
                        closeIcon.classList.remove('hidden');
                        console.log('Mobile menu opened'); // Debug log
                    } else {
                        mobileMenu.classList.add('hidden');
                        menuIcon.classList.remove('hidden');
                        closeIcon.classList.add('hidden');
                        console.log('Mobile menu closed'); // Debug log
                    }
                });

                // Close mobile menu when clicking on a link
                const mobileLinks = mobileMenu.querySelectorAll('a');
                mobileLinks.forEach(link => {
                    link.addEventListener('click', function() {
                        mobileMenu.classList.add('hidden');
                        menuIcon.classList.remove('hidden');
                        closeIcon.classList.add('hidden');
                    });
                });
            } else {
                console.error('Mobile menu elements not found');
            }

            // Desktop user menu toggle functionality
            const userMenuButton = document.getElementById('user-menu-button');
            const userMenu = document.getElementById('user-menu');

            if (userMenuButton && userMenu) {
                userMenuButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    userMenu.classList.toggle('hidden');
                });

                // Close user menu when clicking outside
                document.addEventListener('click', function(event) {
                    if (!userMenuButton.contains(event.target) && !userMenu.contains(event.target)) {
                        userMenu.classList.add('hidden');
                    }
                });
            }

            // Alternative mobile menu toggle function (fallback)
            window.toggleMobileMenu = function() {
                const mobileMenu = document.getElementById('mobile-menu');
                const menuIcon = document.getElementById('menu-icon');
                const closeIcon = document.getElementById('close-icon');
                
                if (mobileMenu && menuIcon && closeIcon) {
                    const isHidden = mobileMenu.classList.contains('hidden');
                    
                    if (isHidden) {
                        mobileMenu.classList.remove('hidden');
                        menuIcon.classList.add('hidden');
                        closeIcon.classList.remove('hidden');
                    } else {
                        mobileMenu.classList.add('hidden');
                        menuIcon.classList.remove('hidden');
                        closeIcon.classList.add('hidden');
                    }
                }
            };
        });