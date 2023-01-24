import { Component } from "./component.js";
import { socketio } from "./utils.js";

export var Meld = (function () {
  var meld = {};  // contains all methods exposed publicly in the meld object
  const components = {};

  /*
    Initializes the meld object.
    */
  meld.init = function (_messageUrl) { //TODO _messageUrl is not used

    socketio.on('meld-response', function(responseJson) {
      console.debug('New meld-reponse received');
      if (!responseJson) {
        return
      }
      if (responseJson.error) {
        console.error(responseJson.error);
        return
      }
      if (!components[responseJson.id])
        return
      else if(components[responseJson.id].actionQueue.length > 0)
        return

      if (responseJson.redirect) {
        window.location.href = responseJson.redirect.url;
      }

      let component = components[responseJson.id];
      if (component ){
        component.onResponseReceived(responseJson.data, responseJson.dom);
      }
    });

    socketio.on('meld-event', function(payload) {
      var event = new CustomEvent(payload.event, { detail: payload.message })
      document.dispatchEvent(event)
    });
  }


/*
    Initializes the component.
    */
meld.componentInit = function (args) {
  const component = new Component(args);
  component.registerManager(this);
  console.log(component.id);
  socketio.emit(
    // 'meld-init', component.name,
    'meld-init', component.id,
    (response) => {
      Object.entries(response).forEach(([eventName, funcNames]) => {
        /**
         * Add the custom listeners from the python class
         * This separate helper function is needed because "this" doesn't
         * work in the socketio.emit callback (it refers to the socketio
         * object).
         */
        component.attachedCustomEvents.push(eventName)
        funcNames.forEach((funcName) => {
          component.addCustomEventListener(eventName, funcName)
        })
      });
    }
  )
  components[component.id] = component;
};

/*
Handles calling the message endpoint and merging the results into the document.
*/
meld.sendMessage = function(componentName, componentId, componentActionQueue, data, renderDOM) {
  renderDOM = renderDOM !== undefined? renderDOM:true;
  
  socketio.emit(
    'meld-message', 
    {
      'id': componentId,
      'actionQueue': componentActionQueue,
      'componentName': componentName,
      'data': data,
      'renderDOM': renderDOM,
    });
}

return meld;
}());
