/*global ResourceRequest _config*/

var ResourceRequest = window.ResourceRequest || {};

(function reqEC2ScopeWrapper($) {

    var authToken;
    ResourceRequest.authToken.then(function setAuthToken(token) {
        if (token) {
            authToken = token;
        } else {
            window.location.href = 'signin.html';
        }
    }).catch(function handleTokenError(error) {
        alert(error);
        window.location.href = 'signin.html';
    });


    function waittoreloadpage(){
        location.reload();
    }
    

    // Validate the stack input parameters
    function validParams() {
        
        // Get and populate the user created resources
        //getUserTasks();
        cmd      = $('#cmd').val()      ;
        console.log(cmd);
        return true;
    }


    function createResources() {

        cmd     = $('#cmd').val()     ;
        env     = $('#env').val()     ;

        if (validParams()){
            $.ajax({
                method: 'POST',
                //url: _config.api.invokeUrl + '/resourcerequest',
                url: _config.api.invokeUrl + '/runtask',
                headers: {
                    Authorization: authToken
                },
                data: JSON.stringify({
                    Resource: {
                        CMD: cmd,
                        ENV: env,
                    }
                }),
                contentType: 'application/json',
                success: function (result){completeCreateResources (result);} ,
                error: function ajaxError(jqXHR, textStatus, errorThrown) {
                    console.error('Error requesting a resource: ', textStatus, ', Details: ', errorThrown);
                    console.error('Response: ', jqXHR.responseText);
                    alert('An error occured when requesting resources:\n' + jqXHR.responseText);
                }
            });
        }
    }

    function completeCreateResources (result) {
        alert ("Wait for few minutes for you stack to be ready.");
        $('.modal').modal('show');
        $("#runTask").attr("disabled", false);
        setTimeout(waittoreloadpage, 500);
    }

    function terminateTask(taskid) {
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl + '/termtask',
            headers: {
                Authorization: authToken
            },
            data: JSON.stringify({
                Resource: {
                    taskid: taskid,
                }
            }),
            contentType: 'application/json',
            success: function (result){completeStackTerminate (result);},
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting a resource: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting resources:\n' + jqXHR.responseText);
            }
        });
    }
    function completeStackTerminate (result) {
        setTimeout(waittoreloadpage, 500); 
    }

    
    // take a list of jsons object (dataList),  then populate the json values (attValue,attName) into a dropdown list with id=elementId
    function fillUpDropDownList (elementId, dataList, attValue, attName){
       var element = document.getElementById(elementId);
       listLength = dataList.length;
       for(var idx = 0; idx < listLength ; idx++) {
            var datenow = dataList[idx][attName]
            var command = dataList[idx]["command"]            
            var env = dataList[idx]["env"]

            var option = '<option value="'+ dataList[idx][attValue] +'">'+ datenow +'</option>'; 
            $(option).appendTo(element);
            //$(option).appendTo(element).sort(function(a, b){return b - a});
            //$(option).appendTo(element).sort();
            //$('#span-select').textContent = "firas";
            $('.modal').modal('hide');
       }
    }

    // Retrieve user resources , stacks created by the user
    function getUserTasks() {
        $.ajax({
            method: 'GET',
            url: _config.api.invokeUrl + '/getusertasks',
            headers: {
                Authorization: authToken
            },
            contentType: 'application/json',
            success: function (result){fillupUsersResFields (result);} ,
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting a resource: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting resources:\n' + jqXHR.responseText);
            }
        });
    }
    


function myFunction() {
  points.sort(function(a, b){return b - a});
  document.getElementById("demo").innerHTML = points;
}

    //Parse the result to a drop down list
    function fillupUsersResFields (result) {
        if (result){
            var resultJSON = result;
            if (resultJSON['resources']){
                fillUpDropDownList('taskList', resultJSON['resources'], "taskid", "datenow","command","environ");
                var stackno = $("#taskList").children('option').length;
                if (stackno > 0){ 
                    $("#stacksdiv select option:last").attr("selected", "selected").show();
                    stackInfo($("#taskList").val(), "tasks");
                }
            }
        }
    }

    // Information about the selected stack ID 
    function stackInfo(taskid,taskstable){
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl + '/infotask',
            headers: {
                Authorization: authToken
            },
            data: JSON.stringify({
                Resource: {
                    taskid: taskid,
                    taskstable: taskstable,
                }
            }),
            contentType: 'application/json',
            success: function (result){completeStackInfos (result,taskstable);},
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting a resource: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting resources:\n' + jqXHR.responseText);
            }
        });
    }

    //Parse the result and inserted to a table
    function completeStackInfos (result,stackstable) {
        console.log(result);
        if (result['url']['output']){
            document.getElementById("output").setAttribute("href",result['url']['output']);
        }
        else {
            document.getElementById("output").removeAttribute("href");
        }
        if (result['url']['error']){
            document.getElementById("error").setAttribute("href",result['url']['error']);
        }
        else {
            document.getElementById("error").removeAttribute("href");
        }
        document.getElementById("taskcmd").value=result['response']['command'];
        document.getElementById("taskenv").value=result['response']['environ'];

    }

    
    function initTags() {
        $("#stacksdiv").hide();
    }
    
    // Register click handler for #request button
    $(function onDocReady() {
        
        // Initiate 
        //initTags()
	
        // Get and populate the user created resources
        getUserTasks();

        $('#runTask').click(handleCreateStackClick);
        //$('#spin').click(handleSpinnerClick);

        $('#taskTerminate').click(handleTerminateTaskClick);
        $('#taskList').change(handleTaskInfoClick);
        $('#taskList').click(handleTaskInfoClick);
        
        $('#signOut').click(function() {
            ResourceRequest.signOut();
            alert("You have been signed out.");
            window.location = "signin.html";
        });

        ResourceRequest.authToken.then(function updateAuthMessage(token) {
            if (token) {
                displayUpdate('You are authenticated. Click to see your <a href="#authTokenModal" data-toggle="modal">auth token</a>.');
                $('.authToken').text(token);
            }
        });

        if (!_config.api.invokeUrl) {
            $('#noApiMessage').show();
        }
    });

    function handleTaskInfoClick(event) {
        var taskid = $('#taskList').val();
        stackInfo(taskid, "tasks");
    }


    function handleCreateStackClick(event) {
        //$("#runTask").attr("disabled", true);
        createResources();
    }

    /*function handleSpinnerClick() {
       $('.modal').modal('show');
       setTimeout(function () {
        console.log('hejsan');
        $('.modal').modal('hide');
       }, 3000);
    }*/


    function handleTerminateTaskClick(event) {
        var taskscount = $("#taskList").children('option').length;
        if (taskscount > 0){
            terminateTask($("#taskList").val());
        }
        else {
            alert("Select the Stack first");
        }
    }

    function displayUpdate(text) {
        $('#updates').append($('<li>' + text + '</li>'));
    }

}(jQuery));
