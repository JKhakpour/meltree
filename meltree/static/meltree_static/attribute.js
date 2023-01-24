/**
 * Encapsulate DOM element attribute for meld-related information.
 */
export class Attribute {
  constructor(attribute) {
    this.attribute = attribute;
    this.name = this.attribute.name;
    this.value = this.attribute.value;
    this.isMeld = false;
    this.isModel = false;
    this.isField = false;
    this.isPoll = false;
    this.isLoading = false;
    this.isTarget = false;
    this.isKey = false;
    this.isPK = false;
    this.isError = false;
    this.modifiers = {};
    this.eventType = null;

    this.init();
  }

  /**
   * Init the attribute.
   */
  init() {
    if (this.name.startsWith("meld:")) {
      this.isMeld = true;
      this.name = this.name || "";

      if ( this.name.indexOf(":model") > -1 ) {
        this.isModel = true;
      } else if ( this.name.indexOf(":field") > -1 ) {
        this.isField = true;
      } else if ( this.name.indexOf(":db") > -1 ) {
        this.isDb = true;
      } else if ( this.name.indexOf(":poll") > -1 ) {
        this.isPoll = true;
      } else if ( this.name.indexOf(":loading") > -1 ) {
        this.isLoading = true;
      } else if ( this.name.indexOf(":target") > -1 ) {
        this.isTarget = true;
      } else if (this.name === "meld:key") {
        this.isKey = true;
      } else if (this.name === "meld:pk") {
        this.isPK = true;
      } else if ( this.name.indexOf(":error:") > -1 ) {
        this.isError = true;
      } else {
        const actionEventType = this.name.replace("meld:", "");

        if (
          actionEventType !== "id" &&
          actionEventType !== "name" &&
          actionEventType !== "checksum"
        ) {
          this.eventType = actionEventType;
        }
      }

      let potentialModifiers = this.name;

      if (this.eventType) {
        potentialModifiers = this.eventType;
      }

      // Find modifiers and any potential arguments
      potentialModifiers
        .split(".")
        .slice(1)
        .forEach((modifier) => {
          const modifierArgs = modifier.split("-");
          this.modifiers[modifierArgs[0]] =
            modifierArgs.length > 1 ? modifierArgs[1] : true;

          // Remove any modifier from the event type
          if (this.eventType) {
            this.eventType = this.eventType.replace(`.${modifier}`, "");
          }
        });
    }
  }
}
