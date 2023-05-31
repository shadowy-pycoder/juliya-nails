// receive information about the entry
// fill selected options according to list of services in the fetched entry
// fill the entry date
// fill the entry time and create other options like in the "create entry" module

const entryToEdit = window.location.pathname.split('/').pop();
const editEntryBtn = document.querySelector('.edit-entry-btn');
editEntryBtn.disabled = true; // this will protect from accidential sending of incorrect information
const timePicker = document.querySelector('#timepicker');
const timeSelector = document.createElement('select');
const datePicker = document.querySelector('#datepicker');
let option = null;

timeSelector.classList.add('form-control', 'timeselector');
timePicker.insertAdjacentElement('afterend', timeSelector);
timeSelector.hidden = true;

timeSelector.addEventListener('change', () => {
    timePicker.value = timeSelector.value; //timepicker always holds value no matter what
    editEntryBtn.disabled = false;
});

// fetch current entry function
async function getEntry(entryId) {
    const response = await fetch(`/api/v1/entries/${entryId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}


// show information about the entry on page load
window.addEventListener("load", (event) => {
    getEntry(entryToEdit).then(currentEntry => {
        if (!window.location.hash) {
            window.location = window.location + '#loaded';
            window.location.reload();
        } // reload page twice to correctly load select2 options
        servicesToSelect(currentEntry); // preselect options for better UX
        datePicker.value = currentEntry.date; // preselect date
        timePicker.value = currentEntry.time.slice(0, 5); // preselect time for better UX
        // list number of availbale time windows, should include time window for current entry
        getEntries(currentEntry.date).then(entries => showEntries(entries, currentEntry));
    });
});


function servicesToSelect(entry) {
    const services = entry.services.map(service => service.id);
    const multiSelect = document.querySelector('#multiselect');
    const optionEls = multiSelect.querySelectorAll('option');
    optionEls.forEach((option) => {
        option.selected = services.includes(parseInt(option.value));
        option.dispatchEvent(new Event('change'));
    });
}

flatpickr("#timepicker", {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    time_24hr: true,
    minTime: "8:00",
    maxTime: "20:00",
    minuteIncrement: 30,

});

flatpickr("#datepicker", {
    altInput: true,
    altFormat: "F j, Y",
    dateFormat: "Y-m-d",
    minDate: "today",
    showMonths: 2,
    onChange: function (selectedDates, dateStr, instance) {
        getEntry(entryToEdit).then(currentEntry => {
            getEntries(instance.element.value).then(result => showEntries(result, currentEntry));
        });
    }
});

$('#multiselect').select2({
    theme: "bootstrap-5",
    width: $(this).data('width') ? $(this).data('width') : $(this).hasClass('w-100') ? '100%' : 'style',
    placeholder: $(this).data('placeholder'),
    closeOnSelect: false,
    tags: true,
    allowClear: true,
});

$('#multiselect').on('change', () => {
    getEntry(entryToEdit).then(currentEntry => {
        getEntries(datePicker.value).then(result => showEntries(result, currentEntry));
    });
});


function retrieveServices() {
    const multiSelect = document.querySelector('#multiselect');
    const selected = Array.from(multiSelect.options)
        .filter(option => option.selected)
        .map(option => option.value);
    return selected;
}

async function getEntries(date) {
    const response = await fetch(`/api/v1/entries?date=${date}&sort=time`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function getServicesDuration(idArray) {
    const duration = [];
    const response = await fetch('/api/v1/services?fields=id,duration', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    const services = await response.json();
    for (let service of services.results) {
        if (idArray.includes((service.id).toString())) {
            duration.push(parseFloat(service.duration));
        }
    }
    return duration.reduce((a, b) => a + b, 0);
}

function generateOption(startDate, adjDuration) {
    startHours = startDate.getHours().toString().padStart(2, '0');
    startMinutes = startDate.getMinutes().toString().padStart(2, '0');
    endDate = new Date(startDate.getTime() + adjDuration);
    endHours = endDate.getHours().toString().padStart(2, '0');
    endMinutes = endDate.getMinutes().toString().padStart(2, '0');
    return [`${startHours}:${startMinutes}`, `${endHours}:${endMinutes}`];
}

function showEntries(data, currentEntry) {
    if (!data.results.length) {
        timePicker.hidden = false;
        timeSelector.hidden = true;
        editEntryBtn.disabled = false;
        timePicker.value = currentEntry.time.slice(0, 5);
    } else {
        while (timeSelector.firstChild) {
            timeSelector.firstChild.remove();
        }
        const services = retrieveServices();
        if (!services.length) {
            return;
        }
        getServicesDuration(services).then(result => {
            let entryArray = data.results.map((x) => x); // make a copy of entry array
            const entriesDate = entryArray[0].date; // retrieve actual day to calculate 8:00 and 20:00 of the day in milliseconds
            if (currentEntry.date === entriesDate) {
                // we should ignore current entry when calculating time windows
                entryArray = entryArray.filter(entry => entry.timestamp !== currentEntry.timestamp);
                if (!entryArray.length) { // edge case: use timepicker instead
                    timePicker.hidden = false;
                    timeSelector.hidden = true;
                    editEntryBtn.disabled = false;
                    timePicker.value = currentEntry.time.slice(0, 5);
                    return;
                }
            }
            timeSelector.hidden = false;
            timePicker.hidden = true;
            option = new Option('Select your option', '', true, true);
            option.disabled = true;
            timeSelector.append(option);
            editEntryBtn.disabled = true;
            const startDay = new Date(entriesDate).setHours(8, 0); // start of the day in milliseconds
            const endDay = new Date(entriesDate).setHours(20, 0); // end of the day in milliseconds
            const secondsBefore = new Date(entryArray[0].timestamp * 1000) - startDay; // number of milliseconds before the very first entry
            const secondsAfter = endDay - new Date(entryArray[entryArray.length - 1].ending_time * 1000); // number of milliseconds after the last entry, can be negative
            const adjDuration = result * 3600 * 1000; // convert duration to milliseconds
            let nIntervals = null; // number of intervals that is used to calculate possible entry intervals
            let startDate = null;
            let startTime = null;
            let endTime = null;

            for (let index = 0; index < entryArray.length; index++) {
                const entryStart = new Date(entryArray[index].timestamp * 1000);
                const prevEntryEnd = new Date(entryArray[index - 1]?.ending_time * 1000);

                if (index === 0) { // edge case: first entry
                    if (secondsBefore >= adjDuration) { // can we serve the client before the first entry of the day?
                        nIntervals = (secondsBefore - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date(startDay + 1800 * 1000 * i);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            option = new Option(`${startTime}-${endTime}`, startTime);
                            timeSelector.append(option);
                        }
                    }
                    if (entryArray.length === 1) {
                        if (secondsAfter >= adjDuration) { // offer intervals before 20:00
                            nIntervals = (secondsAfter - adjDuration) / 1800 / 1000 + 1;
                            for (let i = 0; i < nIntervals; i++) {
                                startDate = new Date((entryArray[index].ending_time + 1800 * i) * 1000);
                                [startTime, endTime] = generateOption(startDate, adjDuration);
                                option = new Option(`${startTime}-${endTime}`, startTime);
                                timeSelector.append(option);
                            }
                        } else if (secondsAfter > 0 && secondsAfter < adjDuration) { // offer a single interval only
                            startDate = new Date(entryArray[index].ending_time * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            option = new Option(`${startTime}-${endTime}`, startTime);
                            timeSelector.append(option);
                        }
                    }
                } else if (index === entryArray.length - 1) { // edge case: last entry
                    if (entryStart - prevEntryEnd >= adjDuration) {
                        nIntervals = (entryStart - prevEntryEnd - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date((entryArray[index - 1].ending_time + 1800 * i) * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            option = new Option(`${startTime}-${endTime}`, startTime);
                            timeSelector.append(option);
                        }
                    }
                    if (secondsAfter >= adjDuration) {
                        nIntervals = (secondsAfter - adjDuration) / 1800 / 1000 + 1;
                        for (let i = 0; i < nIntervals; i++) {
                            startDate = new Date((entryArray[index].ending_time + 1800 * i) * 1000);
                            [startTime, endTime] = generateOption(startDate, adjDuration);
                            option = new Option(`${startTime}-${endTime}`, startTime);
                            timeSelector.append(option);
                        }
                    } else if (secondsAfter > 0 && secondsAfter < adjDuration) {
                        startDate = new Date(entryArray[index].ending_time * 1000);
                        [startTime, endTime] = generateOption(startDate, adjDuration);
                        option = new Option(`${startTime}-${endTime}`, startTime);
                        timeSelector.append(option);
                    }
                } else if (entryStart - prevEntryEnd >= adjDuration) { // check if we have a free time between entries, it will deoend on calculated duration
                    nIntervals = (entryStart - prevEntryEnd - adjDuration) / 1800 / 1000 + 1;
                    for (let i = 0; i < nIntervals; i++) {
                        startDate = new Date((entryArray[index - 1].ending_time + 1800 * i) * 1000);
                        [startTime, endTime] = generateOption(startDate, adjDuration);
                        option = new Option(`${startTime}-${endTime}`, startTime);
                        timeSelector.append(option);
                    }
                }
            }
            //next code here
            if (timeSelector.children.length === 1) { // means 'select time' option only
                timeSelector.firstChild.remove();
                option = new Option('Choose different day or time', '', true, true);
                option.disabled = true;
                timeSelector.append(option);
                editEntryBtn.disabled = true;
            }
        });
    }
}