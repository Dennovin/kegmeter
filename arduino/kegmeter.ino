/* -*- mode: c -*- */

#define NUM_PINS_TAP 4
#define NUM_PINS_TEMP 2
#define PIN_LED 11

#define PIN_NUM_TAP(x) (21 - x)
#define PIN_NUM_TEMP(x) (21 - NUM_PINS_TAP - x)

#define NUM_PINS (NUM_PINS_TAP + NUM_PINS_TEMP)

const int pin_bytes = sizeof(uint64_t);
const int bufsize = 8 + (NUM_PINS * pin_bytes);

volatile uint64_t pulses[NUM_PINS_TAP];
uint8_t last_state[NUM_PINS_TAP];
byte buffer[bufsize] = {0};

void setup() {
  Serial.begin(9600);

  for(int i = 0; i < NUM_PINS_TAP; i++) {
    pinMode(PIN_NUM_TAP(i), INPUT_PULLUP);
    pulses[i] = 0;
    last_state[i] = digitalRead(PIN_NUM_TAP(i));
  }

  for(int i = 0; i < NUM_PINS_TEMP; i++) {
    pinMode(PIN_NUM_TEMP(i), INPUT);
  }

  OCR0A = 0xAF;
  TIMSK0 |= _BV(OCIE0A); // what

  buffer[0] = bufsize;
  buffer[1] = NUM_PINS_TAP;
  buffer[2] = NUM_PINS_TEMP;
  buffer[3] = NUM_PINS;
}

SIGNAL(TIMER0_COMPA_vect) {
  for(int i = 0; i < NUM_PINS_TAP; i++) {
    uint8_t state = digitalRead(PIN_NUM_TAP(i));

    if(state != last_state[i]) {
      pulses[i]++;
    }

    last_state[i] = state;
  }
}

void loop() {
  uint64_t tmp;

  if(Serial.available() > 0) {
    Serial.read();
    digitalWrite(PIN_LED, HIGH);

    for(int i = 0; i < NUM_PINS_TAP; i++) {
      tmp = pulses[i];
      memcpy(&buffer[(i + 1) * pin_bytes], &tmp, pin_bytes);

      pulses[i] = 0;
    }

    for(int i = 0; i < NUM_PINS_TEMP; i++) {
      tmp = (uint64_t)analogRead(PIN_NUM_TEMP(i));
      memcpy(&buffer[(i + 1 + NUM_PINS_TAP) * pin_bytes], &tmp, pin_bytes);
    }

    Serial.write(buffer, bufsize);
  }
  else {
    digitalWrite(PIN_LED, LOW);
  }

  delay(100);
}



