// Learning Room
const $LRLessonList = $('#LRLessonList');
const $toSCInputText = $('#toSCInputText');
const $toTutorInputText = $('#toTutorInputText');
const $scChatbox = $('#scChatbox');
const $tutorChatbox = $('#tutorChatbox');
let lessonList = [];
let sortedWordsArray = [];
let wordDict = {};

function scrollToBottom() {
    $('.chatbox').scrollTop($('.chatbox')[0].scrollHeight);
}

function sendMessage(role) {
    const endpoint = `/chatbot/${role}`;
    const lessonID = $LRLessonList.val();
    if (role == 'sc') {

        $elmid = $scChatbox;
        userText = $toSCInputText.val();
        $toSCInputText.val('');

    }
    if (role == 'tutor') {
        $elmid = $tutorChatbox;
        userText = $toTutorInputText.val();
        $toTutorInputText.val('');

    }

    if (userText == '') return;

    const userFormatText = `
    <div class="msg_user_container">
            <div class="msg_user">
                        ${userText}
            </div>
    </div>`
    $elmid.append(userFormatText);
    scrollToBottom();

    $.ajax({
        type: 'POST',
        url: endpoint,
        data: JSON.stringify({
            'userText': userText,
            'lessonID': lessonID,
        }),
        contentType: 'application/json',
        success: function (response) { 
            const toUserFormatText = `
                <div class="msg_bot_container">
                        <div class="msg_bot">
                            ${response.toUserText}
                        </div>
                </div>`
            $elmid.append(toUserFormatText);
            scrollToBottom();
        },
    
    });

}

function loadConversation() {
    const lessonID = $LRLessonList.val();
    $.ajax({
        type: 'POST',
        url: '/load_conversation',
        data: JSON.stringify({
            'lessonID': lessonID,
        }),
        contentType: 'application/json',
        success: function (response) {
            $scChatbox.empty();
            $tutorChatbox.empty();
            $scChatbox.append(`
            <div class="msg_bot_container">
                <div class="msg_bot">
                <strong>🦉</strong>
                Hello, I am Simu. How can I help you today?
                </div>
            </div>`);
            $tutorChatbox.append(`
            <div class="msg_bot_container">
                <div class="msg_bot">
                    <strong>📚</strong>
                    Hello, I am your tutor. How can I assist you today?
                </div>
            </div>`);


            const conversations = response.conversations;
            conversations.forEach(function (conversation) {
                let rpUniCode = '';
                if (conversation.agent_role == 'sc') {
                    rpUniCode = '🦉';
                } else {
                    rpUniCode = '📚';
                }

                const formatedConversation = `
                    <div class="msg_user_container">
                            <div class="msg_user">
                                ${conversation.user_input}
                            </div>
                    </div>

                    <div class="msg_bot_container">
                            <div class="msg_bot">
                                <strong>${rpUniCode}</strong>
                                ${conversation.response}
                            </div>
                    </div>`
                if (conversation.agent_role == 'sc') {
                    $scChatbox.append(formatedConversation);
                }
                else {
                    $tutorChatbox.append(formatedConversation);
                }
            })
            scrollToBottom();
        },
    });
}

function clearChat() {
    const lessonID = $LRLessonList.val();

    $.ajax({
        type: 'POST',
        url: "/clear_chat",
        data: JSON.stringify({
            'lessonID': lessonID,
        }),
        contentType: 'application/json',
        success: function (response) { 
            $scChatbox.empty();
            $tutorChatbox.empty();
        },
    });

}

// Lesson Designer

const $userPrompt = $('#userPrompt');
const $lessonTitle = $('#lessonTitle');
const $lessonDesc = $('#lessonDesc');
const $tutorPrompt = $('#tutorPrompt');
const $scPrompt = $('#scPrompt');
const $lessonDesignBtn = $('#lessonDesignBtn');
const $lessonSaveBtn = $('#lessonSaveBtn');
const $lessonDeleteBtn = $('#lessonDeleteBtn');
const $clearContentsBtn = $('#clearContentsBtn');
const $LDSideNav = $('#LDSideNav');
const $searchWord = $('#searchWord');

function loadLDContents(lesson){
    $userPrompt.val(lesson.userPrompt).prop('readonly', false);
    $lessonTitle.val(lesson.lessonTitle).prop('readonly', false);
    $lessonDesc.val(lesson.lessonDesc).prop('readonly', false);
    $tutorPrompt.val(lesson.tutorPrompt).prop('readonly', false);
    $scPrompt.val(lesson.scPrompt).prop('readonly', false);
    $lessonDesignBtn.prop('disabled', false).text('Design');
    $lessonSaveBtn.prop('disabled', false).text('Save');
    $lessonDeleteBtn.prop('disabled', true).text('Delete');
    $clearContentsBtn.prop('disabled', false).text('Create New Lesson');

    if(lesson.lessonID > 0){
        $lessonDeleteBtn.attr('onclick', `deleteLesson(${lesson.lessonID})`).prop('disabled', false);
        $userPrompt.prop('readonly', true);
        $lessonDesignBtn.prop('disabled', true);
        $lessonSaveBtn.prop('disabled', true);
    }

}

function clearLDContents(){
    $userPrompt.val('').prop('readonly', false);
    $lessonTitle.val('').prop('readonly', true);
    $lessonDesc.val('').prop('readonly', true);
    $tutorPrompt.val('').prop('readonly', true);
    $scPrompt.val('').prop('readonly', true);
    $lessonDesignBtn.prop('disabled', false).text('Design');
    $lessonSaveBtn.prop('disabled', true).text('Save');
    $lessonDeleteBtn.prop('disabled', true).text('Delete');
    $clearContentsBtn.prop('disabled', true).text('Create New Lesson');
}

function updateLRLessonList(lessons){
    $LRLessonList.empty();
    lessons.forEach(function(lesson){
        $('<option>').attr('value', lesson.lessonID).text(lesson.lessonTitle).appendTo($LRLessonList);
    });
}

function updatLDLessonList(lessons){
    $LDSideNav.empty();
    lessons.forEach(function(lesson){
        const $lessonLink = $('<a>')
        .addClass('nav-link')
        .attr('href', `#`)
        .attr('onclick', `loadLesson(${lesson.lessonID})`)
        .text(lesson.lessonTitle);
        $('<li>').addClass('nav-item').append($lessonLink).appendTo($LDSideNav);
    });
}

function updateLessonList(lessons){
    updateLRLessonList(lessons);
    updatLDLessonList(lessons);
}

function designLesson() {
    const userPrompt = $userPrompt.val();

    if (userPrompt == '') return;   


    $.ajax({
        type : 'POST',
        url : '/design_lesson',
        data : JSON.stringify({
            'userPrompt' : userPrompt
        }),
        contentType : 'application/json',
        success : function(response) {
            loadLDContents(response);
        },
        beforeSend : function() {
            $lessonDesignBtn.prop('disabled', true).text('Processing...');
        }
    })

}

function saveLesson() {
    if ($userPrompt.val() == '' || 
        $lessonTitle.val() == '' || 
        $lessonDesc.val() == '' || 
        $tutorPrompt.val() == '' || 
        $scPrompt.val() == '') 
        return;

    $.ajax({
        type : 'POST',
        url : '/save_lesson',
        data : JSON.stringify({
            'userPrompt' : $userPrompt.val(),
            'lessonTitle' : $lessonTitle.val(),
            'lessonDesc' : $lessonDesc.val(),
            'tutorPrompt' : $tutorPrompt.val(),
            'scPrompt' : $scPrompt.val()
        }),
        contentType : 'application/json',
        success : function(response) {
            updateLessonList(response.lessonList);
            clearLDContents();
            updateIndex();
        },
        beforeSend : function() {
            $lessonSaveBtn.prop('disabled', true).text('Saving...');
        }
    })
}

function loadLesson(lessonID) {
    $.ajax({
        type : 'POST',
        url : '/load_lesson',
        data : JSON.stringify({
            'lessonID' : lessonID
        }),
        contentType : 'application/json',
        success : function(response) {
            loadLDContents(response);
        }
        
    })
}

function deleteLesson(lessonID) {
    $.ajax({
        type : 'POST',
        url : '/delete_lesson',
        data : JSON.stringify({
            'lessonID' : lessonID
        }),
        contentType : 'application/json',
        success : function(response) {
            clearLDContents();
            updateLessonList(response.lessonList);
            updateIndex();
        }
    })
}


function createWordDict(lessonList){
    let wordDict = {};
    for (let i = 0; i < lessonList.length; i++) {
        const lessonID = lessonList[i].lessonID;
        const lessonTitle = lessonList[i].lessonTitle;
        let words = lessonTitle.split(' ');
        words = words.map(word => word.toLowerCase());
        for (let j = 0; j < words.length; j++) {
            if (!wordDict[words[j]]) {
                wordDict[words[j]] = [{"lessonID":lessonID, "lessonTitle":lessonTitle}];
            } else {
                wordDict[words[j]].push({"lessonID":lessonID, "lessonTitle":lessonTitle});
            }
        }
    }
    return wordDict;
}

// function for sorting wordIndex using merge sort
function mergeSort(arr) {
    if (arr.length <= 1) return arr;
    const mid = Math.floor(arr.length / 2);
    const left = arr.slice(0, mid);
    const right = arr.slice(mid);
    return merge(mergeSort(left), mergeSort(right));
}

function merge(left, right) {
    let result = [];
    let leftIndex = 0;
    let rightIndex = 0;

    while (leftIndex < left.length && rightIndex < right.length) {
        if (left[leftIndex][0] < right[rightIndex][0]) {
            result.push(left[leftIndex]);
            leftIndex++;
        } else {
            result.push(right[rightIndex]);
            rightIndex++;
        }
    }
    return result.concat(left.slice(leftIndex)).concat(right.slice(rightIndex));
}

function getLDLessonList(){
    const $LDSideNavChildren = $LDSideNav.children();
    let lessonList = [];
    for (let i = 0; i < $LDSideNavChildren.length; i++) {
        const lesson = $LDSideNavChildren[i].children[0];
        const lessonID = lesson.getAttribute('onclick').split('(')[1].split(')')[0];
        lessonList.push({"lessonID":lessonID, "lessonTitle":lesson.innerText.trim()});
    }
    return lessonList;
}

// function for searching word in wordDict using binary search
function binarySearch(){
    const word = $searchWord.val().toLowerCase();
    let left = 0;
    let right = sortedWordsArray.length - 1;
   
    while (left <= right) {
        let mid = Math.floor((left + right) / 2);
        if (sortedWordsArray[mid][0] === word) {
            updatLDLessonList(sortedWordsArray[mid][1]);
            return;
        } else if (sortedWordsArray[mid][0] < word) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    updatLDLessonList(lessonList);
}

function updateIndex(){
    lessonList = getLDLessonList();
    wordDict = createWordDict(lessonList);
    sortedWordsArray = mergeSort(Object.entries(wordDict));
}
$(document).ready(function(){
    updateIndex();
});