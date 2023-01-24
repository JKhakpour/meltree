export var socketio = io();
/*
Traverse the DOM looking for child elements.
*/
export function walk(el, callback) {
  var walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, null, false);

  while (walker.nextNode()) {
    // TODO: Handle sub-components
    callback(walker.currentNode);
  }
}

/*
A simple shortcut for querySelector that everyone loves.
*/
export function $(selector, scope) {
  if (scope == undefined) {
    scope = document;
  }

  return scope.querySelector(selector);
}

/**
 * Checks if an object is empty. Useful to check if a dictionary has a value.
 */
export function isEmpty(obj) {
  return (
    typeof obj === "undefined" ||
    obj === null ||
    (Object.keys(obj).length === 0 && obj.constructor === Object)
  );
}

