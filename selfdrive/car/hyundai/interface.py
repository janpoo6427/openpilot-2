#!/usr/bin/env python3
from cereal import car
from selfdrive.config import Conversions as CV
from selfdrive.car.hyundai.values import Ecu, ECU_FINGERPRINT, CAR, FINGERPRINTS, Buttons
from selfdrive.car import STD_CARGO_KG, scale_rot_inertia, scale_tire_stiffness, is_ecu_disconnected, gen_empty_fingerprint
from selfdrive.car.interfaces import CarInterfaceBase
from selfdrive.controls.lib.pathplanner import LANE_CHANGE_SPEED_MIN
from common.params import Params

GearShifter = car.CarState.GearShifter
EventName = car.CarEvent.EventName
ButtonType = car.CarState.ButtonEvent.Type

class CarInterface(CarInterfaceBase):
  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)
    self.cp2 = self.CS.get_can2_parser(CP)
    self.mad_mode_enabled = Params().get('MadModeEnabled') == b'1'
    self.lkas_button_alert = False

  @staticmethod
  def compute_gb(accel, speed):
    return float(accel) / 3.0

  @staticmethod
  def get_params(candidate, fingerprint=gen_empty_fingerprint(), has_relay=False, car_fw=[]):  # pylint: disable=dangerous-default-value
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint, has_relay)

    ret.carName = "hyundai"
    ret.safetyModel = car.CarParams.SafetyModel.hyundaiLegacy
    if candidate in [CAR.SONATA]:
      ret.safetyModel = car.CarParams.SafetyModel.hyundai

    # Most Hyundai car ports are community features for now
    ret.communityFeature = candidate not in [CAR.SONATA]

    ret.steerActuatorDelay = 0.1  # Default delay
    ret.steerRateCost = 0.5
    ret.steerLimitTimer = 0.8
    tire_stiffness_factor = 1.

    # genesis
    if candidate == CAR.GENESIS:
      ret.mass = 1900. + STD_CARGO_KG
      ret.wheelbase = 3.01
      ret.minSteerSpeed = 60 * CV.KPH_TO_MS
    elif candidate == CAR.GENESIS_G70:
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.84
    elif candidate == CAR.GENESIS_G80:
      ret.mass = 1855. + STD_CARGO_KG
      ret.wheelbase = 3.01
    # g90
    
    
    elif candidate == CAR.GENESIS_G90:
      ret.mass = 2290. + STD_CARGO_KG
      ret.wheelbase = 3.45
    
    
    
    # hyundai
    elif candidate in [CAR.SANTA_FE]:
      ret.mass = 1694 + STD_CARGO_KG
      ret.wheelbase = 2.766
    elif candidate in [CAR.SONATA, CAR.SONATA_HEV]:
      ret.mass = 1513. + STD_CARGO_KG
      ret.wheelbase = 2.84
      tire_stiffness_factor = 0.65
    elif candidate in [CAR.SONATA19, CAR.SONATA19_HEV]:
      ret.mass = 4497. * CV.LB_TO_KG
      ret.wheelbase = 2.804
    elif candidate == CAR.PALISADE:
      ret.mass = 1999. + STD_CARGO_KG
      ret.wheelbase = 2.90
    elif candidate in [CAR.ELANTRA, CAR.ELANTRA_GT_I30]:
      ret.mass = 1275. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385    # stiffnessFactor settled on 1.0081302973865127
    elif candidate == CAR.KONA:
      ret.mass = 1275. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.KONA_HEV, CAR.KONA_EV]:
      ret.mass = 1685. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.IONIQ, CAR.IONIQ_EV_LTD]:
      ret.mass = 1490. + STD_CARGO_KG   #weight per hyundai site https://www.hyundaiusa.com/ioniq-electric/specifications.aspx
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.GRANDEUR, CAR.GRANDEUR_HEV]:
      tire_stiffness_factor = 0.8
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.845
    elif candidate == CAR.VELOSTER:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    # kia
    elif candidate == CAR.SORENTO:
      ret.mass = 1985. + STD_CARGO_KG
      ret.wheelbase = 2.78
      tire_stiffness_factor = 0.5
    elif candidate == CAR.KIA_SELTOS:
      ret.mass = 1440. + STD_CARGO_KG
      ret.wheelbase = 2.63
      ret.steerRatio = 13.75
      tire_stiffness_factor = 0.5
    elif candidate in [CAR.OPTIMA, CAR.OPTIMA_HEV]:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    elif candidate == CAR.STINGER:
      tire_stiffness_factor = 1.125 # LiveParameters (Tunder's 2020)
      ret.mass = 1825.0 + STD_CARGO_KG
      ret.wheelbase = 2.906 # https://www.kia.com/us/en/stinger/specs
    elif candidate == CAR.FORTE:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    elif candidate == CAR.CEED:
      ret.mass = 1350. + STD_CARGO_KG
      ret.wheelbase = 2.65
      tire_stiffness_factor = 0.5
    elif candidate == CAR.SPORTAGE:
      ret.mass = 1985. + STD_CARGO_KG
      ret.wheelbase = 2.78
    elif candidate in [CAR.NIRO_HEV, CAR.NIRO_EV]:
      ret.mass = 1737. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.CARDENZA, CAR.CARDENZA_HEV]:
      tire_stiffness_factor = 0.6
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.845



    # LQR control by default for lateral control.

    ret.lateralTuning.init('lqr')

    ret.lateralTuning.lqr.scaleBP = [20. * CV.KPH_TO_MS, 50. * CV.KPH_TO_MS]
    ret.lateralTuning.lqr.scaleV = [1700.0, 1500.0]

    ret.lateralTuning.lqr.ki = 0.009

    ret.lateralTuning.lqr.a = [0., 1., -0.22619643, 1.21822268]
    ret.lateralTuning.lqr.b = [-1.92006585e-04, 3.95603032e-05]
    ret.lateralTuning.lqr.c = [1., 0.]
    ret.lateralTuning.lqr.k = [-103.976, 450.]
    ret.lateralTuning.lqr.l = [0.22, 0.318]
    ret.lateralTuning.lqr.dcGain = 0.003

    ret.steerRatio = 13.0
    ret.steerActuatorDelay = 0.2
    ret.steerLimitTimer = 2.5

    ret.steerRateCost = 0.55

    ret.steerMaxBP = [30. * CV.KPH_TO_MS, 60. * CV.KPH_TO_MS]
    ret.steerMaxV = [1.5, 2.5]




    ret.centerToFront = ret.wheelbase * 0.4

    # TODO: get actual value, for now starting with reasonable value for
    # civic and scaling by mass and wheelbase
    ret.rotationalInertia = scale_rot_inertia(ret.mass, ret.wheelbase)

    # TODO: start from empirically derived lateral slip stiffness for the civic and scale by
    # mass and CG position, so all cars will have approximately similar dyn behaviors
    ret.tireStiffnessFront, ret.tireStiffnessRear = scale_tire_stiffness(ret.mass, ret.wheelbase, ret.centerToFront,
                                                                         tire_stiffness_factor=tire_stiffness_factor)

    # no rear steering, at least on the listed cars above
    ret.steerRatioRear = 0.
    ret.steerControlType = car.CarParams.SteerControlType.torque

    ret.longitudinalTuning.kpBP = [0., 10., 40.]
    ret.longitudinalTuning.kpV = [1.2, 0.6, 0.2]
    ret.longitudinalTuning.kiBP = [0., 10., 30., 40.]
    ret.longitudinalTuning.kiV = [0.05, 0.02, 0.01, 0.005]
    ret.longitudinalTuning.deadzoneBP = [0., 40]
    ret.longitudinalTuning.deadzoneV = [0., 0.02]


    # steer, gas, brake limitations VS speed

    ret.gasMaxBP = [0., 10., 40.]
    ret.gasMaxV = [0.5, 0.5, 0.5]
    ret.brakeMaxBP = [0., 20.]
    ret.brakeMaxV = [1., 0.8]

    ret.enableCamera = is_ecu_disconnected(fingerprint[0], FINGERPRINTS, ECU_FINGERPRINT, candidate, Ecu.fwdCamera) or has_relay

    ret.stoppingControl = True
    ret.startAccel = 0.0

    # ignore CAN2 address if L-CAN on the same BUS
    ret.mdpsBus = 1 if 593 in fingerprint[1] and 1296 not in fingerprint[1] else 0
    ret.sasBus = 1 if 688 in fingerprint[1] and 1296 not in fingerprint[1] else 0
    ret.sccBus = 0 if 1056 in fingerprint[0] else 1 if 1056 in fingerprint[1] and 1296 not in fingerprint[1] \
                                                                     else 2 if 1056 in fingerprint[2] else -1
    ret.radarOffCan = ret.sccBus == -1
    ret.openpilotLongitudinalControl = Params().get('LongControlEnabled') == b'1'
    ret.enableCruise = not ret.radarOffCan
    ret.spasEnabled = False
    
    # set safety_hyundai_community only for non-SCC, MDPS harrness or SCC harrness cars or cars that have unknown issue
    if ret.radarOffCan or ret.mdpsBus == 1 or ret.openpilotLongitudinalControl or ret.sccBus == 1 or Params().get('MadModeEnabled') == b'1':
      ret.safetyModel = car.CarParams.SafetyModel.hyundaiCommunity
    return ret

  def update(self, c, can_strings):
    self.cp.update_strings(can_strings)
    self.cp2.update_strings(can_strings)
    self.cp_cam.update_strings(can_strings)

    ret = self.CS.update(self.cp, self.cp2, self.cp_cam)
    ret.canValid = self.cp.can_valid and self.cp2.can_valid and self.cp_cam.can_valid

    if self.CP.enableCruise and not self.CC.scc_live:
      self.CP.enableCruise = False
    elif self.CC.scc_live and not self.CP.enableCruise:
      self.CP.enableCruise = True

    # most HKG cars has no long control, it is safer and easier to engage by main on
    if self.mad_mode_enabled and not self.CC.longcontrol:
      ret.cruiseState.enabled = ret.cruiseState.available
    # some Optima only has blinker flash signal
    if self.CP.carFingerprint == CAR.OPTIMA:
      ret.leftBlinker = bool(self.CS.left_blinker_flash or self.CS.prev_left_blinker and self.CC.turning_signal_timer)
      ret.rightBlinker = bool(self.CS.right_blinker_flash or self.CS.prev_right_blinker and self.CC.turning_signal_timer)

    # turning indicator alert logic
    if (ret.leftBlinker or ret.rightBlinker or self.CC.turning_signal_timer) and ret.vEgo < LANE_CHANGE_SPEED_MIN - 1.2:
      self.CC.turning_indicator_alert = True
    else:
      self.CC.turning_indicator_alert = False

    # LKAS button alert logic: reverse on/off
    #if not self.CS.lkas_error and self.CS.lkas_button_on != self.CS.prev_lkas_button_on:
      #self.CC.lkas_button_on = not self.CC.lkas_button_on
      #self.lkas_button_alert = not self.CC.lkas_button_on

    # low speed steer alert hysteresis logic (only for cars with steer cut off above 10 m/s)
    if ret.vEgo < (self.CP.minSteerSpeed + 0.2) and self.CP.minSteerSpeed > 10.:
      self.low_speed_alert = True
    if ret.vEgo > (self.CP.minSteerSpeed + 0.7):
      self.low_speed_alert = False

    buttonEvents = []
    if self.CS.cruise_buttons != self.CS.prev_cruise_buttons:
      be = car.CarState.ButtonEvent.new_message()
      be.pressed = self.CS.cruise_buttons != 0
      but = self.CS.cruise_buttons if be.pressed else self.CS.prev_cruise_buttons
      if but == Buttons.RES_ACCEL:
        be.type = ButtonType.accelCruise
      elif but == Buttons.SET_DECEL:
        be.type = ButtonType.decelCruise
      elif but == Buttons.GAP_DIST:
        be.type = ButtonType.gapAdjustCruise
      #elif but == Buttons.CANCEL:
      #  be.type = ButtonType.cancel
      else:
        be.type = ButtonType.unknown
      buttonEvents.append(be)
    if self.CS.cruise_main_button != self.CS.prev_cruise_main_button:
      be = car.CarState.ButtonEvent.new_message()
      be.type = ButtonType.altButton3
      be.pressed = bool(self.CS.cruise_main_button)
      buttonEvents.append(be)
    ret.buttonEvents = buttonEvents

    events = self.create_common_events(ret)

    if self.CC.longcontrol and self.CS.cruise_unavail:
      events.add(EventName.brakeUnavailable)
    #if abs(ret.steeringAngle) > 90. and EventName.steerTempUnavailable not in events.events:
    #  events.add(EventName.steerTempUnavailable)
    if self.low_speed_alert and not self.CS.mdps_bus:
      events.add(EventName.belowSteerSpeed)
    if self.CC.turning_indicator_alert:
      events.add(EventName.turningIndicatorOn)
    if self.lkas_button_alert:
      events.add(EventName.lkasButtonOff)
    if self.mad_mode_enabled and not self.CC.longcontrol and EventName.pedalPressed in events.events:
      events.events.remove(EventName.pedalPressed)

  # handle button presses
    for b in ret.buttonEvents:
      # do disable on button down
      if b.type == ButtonType.cancel and b.pressed:
        events.add(EventName.buttonCancel)
      if self.CC.longcontrol and not self.CC.scc_live:
        # do enable on both accel and decel buttons
        if b.type in [ButtonType.accelCruise, ButtonType.decelCruise] and not b.pressed:
          events.add(EventName.buttonEnable)
        if EventName.wrongCarMode in events.events:
          events.events.remove(EventName.wrongCarMode)
        if EventName.pcmDisable in events.events:
          events.events.remove(EventName.pcmDisable)
      elif not self.CC.longcontrol and ret.cruiseState.enabled:
        # do enable on decel button only
        if b.type == ButtonType.decelCruise and not b.pressed:
          events.add(EventName.buttonEnable)

    ret.events = events.to_msg()

    self.CS.out = ret.as_reader()
    return self.CS.out

  def apply(self, c):
    can_sends = self.CC.update(c.enabled, self.CS, self.frame, c.actuators,
                               c.cruiseControl.cancel, c.hudControl.visualAlert, c.hudControl.leftLaneVisible,
                               c.hudControl.rightLaneVisible, c.hudControl.leftLaneDepart, c.hudControl.rightLaneDepart,
                               c.hudControl.setSpeed, c.hudControl.leadVisible)
    self.frame += 1
    return can_sends
