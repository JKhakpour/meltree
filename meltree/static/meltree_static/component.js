import {$, walk, isEmpty, socketio } from "./utils.js";
import { Element } from "./element.js";
import { morph } from "./morph.js"

export class Component {
  constructor(args) {
    this.id = args.id;
    this.name = args.name;
    // this.messageUrl = args.messageUrl;
    // this.csrfTokenHeaderName = args.csrfTokenHeaderName;

    if (this.name.includes(".")) {
      const names = this.name.split(".");
      this.name = names[names.length - 2];
    }

    this.data = args.data;

    this.document = args.document || document;
    this.walker = args.walker || walk;

    this.root = undefined;
    this.modelEls = [];
    this.keyEls = [];
    this.loadingEls = [];

    this.actionQueue = [];
    this.activeDebouncers = 0

    this.actionEvents = {};
    this.attachedEventTypes = [];
    this.attachedModelEvents = [];
    this.attachedCustomEvents = [];

    this.init();
    this.refreshEventListeners();
  }

  checkComponentDefer(element, action){
      if (element.model.isDefer) {
          let foundAction = false;

          // Update the existing action with the current value
          this.actionQueue.forEach((a) => {
            if (a.payload.name === element.model.name) {
              a.payload.value = element.getValue();
              foundAction = true;
            }
          });

          // Add the action if not already in the queue
          if (!foundAction) {
            this.actionQueue.push(action);
          }
          return;
      }
    else{
      this.actionQueue.push(action);
      this.queueMessage(element.model);
    }
  }

  registerManager(manager) {
    this.manager = manager;
  }

  addModelEventListener(component, el, eventType) {
    el.addEventListener(eventType, (event) => {
      const element = new Element(event.target, component);

      const action = {
        type: "syncInput",
        payload: {
          name: element.model.name,
          value: element.getValue(),
        },
      };

      this.checkComponentDefer(element, action);
    });
  }

  onResponseReceived(data, dom){
    this._onResponseCallbacks.forEach(callback => {
      console.log(callback.name);
      callback(this, data, dom)
    });
  }

  _onResponseCallbacks = [
    this.updateData,
    this.updateDOM,
  ]

  /**
   * Adds an action event listener to the document for each type of event (e.g. click, keyup, etc).
   * Added at the document level because validation errors would sometimes remove the
   * events when attached directly to the element.
   * @param {Component} component Component that contains the element.
   * @param {string} eventType Event type to listen for.
   */
  addActionEventListener(eventType) {
    this.document.addEventListener(eventType, (event) => {
      let targetElement = new Element(event.target, this);

      // Make sure that the target element is a meld element.
      if (targetElement && !targetElement.isMeld) {
        targetElement = targetElement.getMeldParent();
      }

      if (
        targetElement &&
        targetElement.isMeld &&
        targetElement.actions.length > 0
      ) {
        this.actionEvents[eventType].forEach((actionEvent) => {
          const { action } = actionEvent;
          const { element } = actionEvent;

          if (targetElement.isSame(element)) {
            if (action.isPrevent) {
              event.preventDefault();
            }

            if (action.isStop) {
              event.stopPropagation();
            }

            var method = { type: "callMethod", payload: { name: action.name } };


            if (action.key) {
              if (action.key === event.key.toLowerCase()) {
                this.actionQueue.push(method);
                this.queueMessage(element.model);
                this.handleLoading(targetElement);
              }
            } else {
                this.actionQueue.push(method);
                this.queueMessage(element.model);
                this.handleLoading(targetElement);
            }
          }
        });
      }
    });
  }

  /**
   * Handles loading elements in the component.
   * @param {Element} targetElement Targetted element.
   */
  handleLoading(targetElement) {
    targetElement.handleLoading();

    // Look at all elements with a loading attribute
    this.loadingEls.forEach((loadingElement) => {
      if (loadingElement.target) {
        let targetedEl = $(`#${loadingElement.target}`, this.root);

        if (!targetedEl) {
          this.keyEls.forEach((keyElement) => {
            if (!targetedEl && keyElement.key === loadingElement.target) {
              targetedEl = keyElement.el;
            }
          });
        }

        if (targetedEl) {
          if (targetElement.el.isSameNode(targetedEl)) {
            if (loadingElement.loading.hide) {
              loadingElement.hide();
            } else if (loadingElement.loading.show) {
              loadingElement.show();
            }
          }
        }
      } else if (loadingElement.loading.hide) {
        loadingElement.hide();
      } else if (loadingElement.loading.show) {
        loadingElement.show();
      }
    });
  }

  /*
  * Handles calling the message endpoint and merging the results into the document.
  */
  sendMessage() {
    // Prevent network call when there isn't an action
    if (this.actionQueue.length === 0) {
      return;
    }

    // Prevent network call when the action queue gets repeated
    if (this.currentActionQueue === this.actionQueue) {
      return;
    }

    this.currentActionQueue = this.actionQueue;
    this.actionQueue = [];

    this.manager.sendMessage(
      this.name, 
      this.id,
      this.currentActionQueue,
      this.data
    );
  }

  updateData(component, newData, dom){
    let data = JSON.parse(newData);
    for (var key in data) {
      component.data[key] = data[key];
    }
  }

  /**
   * Adds a custom event listener to the document for the given eventName.
   * @param {string} eventName Name of the custom meld-event to be listened for
   * @param {string} funcName Name of the method to call on the Python Component
   */
  addCustomEventListener(eventName, funcName) {
    this.document.addEventListener(eventName, (event) => {
      const element = new Element(event.target, this);
      var method = { type: "callMethod", payload: { name: funcName, message: event.detail } };
      this.actionQueue.push(method);
      this.queueMessage(element.model);
    });
  }

  queueMessage(model, callback) {
    if (model.debounceTime === -1) {
      this.debounce(150)(this, callback);
    } else {
      this.debounce(model.debounceTime)(this, callback);
    }
  }


  /**
   * Returns a function, that, as long as it continues to be invoked, will not
   * be triggered. The function will be called after it stops being called for
   * N milliseconds. If `immediate` is passed, trigger the function on the
   * leading edge, instead of the trailing.
   * Derived from underscore.js's implementation in https://davidwalsh.name/javascript-debounce-function.
   */
  debounce(wait) {
    return (...args) => {
      const context = this;
      clearTimeout(this.debounce_timer);
      this.debounce_timer = setTimeout(() => {
        this.sendMessage.apply(context, args)
      }, wait);
    };
  }



  /**
   * Initializes the Component.
   */
  init() {
    this.root = $(`[meld\\:id="${this.id}"]`, this.document);

    if (!this.root) {
      throw Error("No id found");
    }

    /**
     * Add the custom listeners from the python class
     * This separate helper function is needed because "this" doesn't
     * work in the socketio.emit callback (it refers to the socketio
     * object).
     */
     function addListeners(component, response) {
      Object.entries(response).forEach(([eventName, funcNames]) => {
        component.attachedCustomEvents.push(eventName)
        funcNames.forEach((funcName) => {
          component.addCustomEventListener(eventName, funcName)
        })
      })
    }

    socketio.emit(
      'meld-init', this.id,
      (response) => addListeners(this, response)
    )
  }

  refreshEventListeners() {
    this.actionEvents = {};
    this.modelEls = [];
    this.dbEls = [];

    walk(this.root, (el) => {
      if (el.isSameNode(this.root)) {
        // Skip the component root element
        return;
      }

      const element = new Element(el, this);

      if (element.isMeld) {
         if ( !isEmpty(element.model)) {
          if (!this.attachedModelEvents.some((e) => e.isSame(element))) {
            this.attachedModelEvents.push(element);
            this.addModelEventListener(this, element.el, element.model.eventType);
          }

          if (!this.modelEls.some((e) => e.isSame(element))) {
            this.modelEls.push(element);
          }
        } else if (!isEmpty(element.loading)) {
          this.loadingEls.push(element);

          // Hide loading elements that are shown when an action happens
          if (element.loading.show) {
            element.hide();
          }
        }

        if (!isEmpty(element.key)) {
          this.keyEls.push(element);
        }

        element.actions.forEach((action) => {
          if (this.actionEvents[action.eventType]) {
            this.actionEvents[action.eventType].push({ action, element });
          } else {
            this.actionEvents[action.eventType] = [{ action, element }];

            if (
              !this.attachedEventTypes.some((et) => et === action.eventType)
            ) {
              this.attachedEventTypes.push(action.eventType);
              this.addActionEventListener(action.eventType);
            }
          }
        });
      }
    });
  }

  updateDOM(scope, data, dom) {
    var componentRoot = $(`[meld\\:id="${scope.id}"]`);
    morph(componentRoot, dom);
    scope.refreshEventListeners()
  }
}

