// Observation-only extension. Calls the archived Mate CC implementation unchanged.
// No random draws, no movement/actuation, no sensor updates, no score edits.
#include "loop-functions/mate/CC/MateCCLoopFunc.h"
#include <argos3/core/control_interface/ci_controller.h>
#include <argos3/plugins/robots/e-puck/control_interface/ci_epuck_ground_sensor.h>
#include <argos3/plugins/robots/e-puck/control_interface/ci_epuck_omnidirectional_camera_sensor.h>
#include <fstream>
#include <iomanip>

class ObservedMateCC : public MateCCLoopFunction {
  std::ofstream trace;
  unsigned postSteps = 0;
 public:
  void Init(TConfigurationNode& node) override {
    MateCCLoopFunction::Init(node);
    trace.open("observer_poses.csv");
    trace << "tick,robot,x,y,yaw,ground_left,ground_center,ground_right,camera_total,camera_cyan,camera_cyan_filtered,score\n";
    trace << std::setprecision(17);
    Record();
  }
  void PostStep() override {
    MateCCLoopFunction::PostStep();
    ++postSteps;
    if(GetSpace().GetSimulationClock() % 100 == 0 || postSteps <= 10) Record();
  }
  void PostExperiment() override {
    Record();
    trace.flush();
    LOG << "ObservedTicks: " << GetSpace().GetSimulationClock()
        << " PostSteps: " << postSteps << " Robots: "
        << GetSpace().GetEntitiesByType("epuck").size() << std::endl;
    MateCCLoopFunction::PostExperiment();
  }
  void Record() {
    auto& robots = GetSpace().GetEntitiesByType("epuck");
    for(auto& item : robots) {
      auto* robot = any_cast<CEPuckEntity*>(item.second);
      auto& anchor = robot->GetEmbodiedEntity().GetOriginAnchor();
      CRadians yaw, pitch, roll;
      anchor.Orientation.ToEulerAngles(yaw,pitch,roll);
      auto& control = robot->GetControllableEntity().GetController();
      auto* ground = control.GetSensor<CCI_EPuckGroundSensor>("epuck_ground");
      auto* camera = control.GetSensor<CCI_EPuckOmnidirectionalCameraSensor>("epuck_omnidirectional_camera");
      auto& g = ground->GetReadings();
      auto& blobs = camera->GetReadings().BlobList;
      unsigned cyan = 0, filtered = 0;
      for(auto* blob: blobs) if(blob->Color == CColor::CYAN) {
        ++cyan;
        if(blob->Distance >= 5 && blob->Distance <= 30) ++filtered;
      }
      trace << GetSpace().GetSimulationClock() << ',' << robot->GetId() << ','
            << anchor.Position.GetX() << ',' << anchor.Position.GetY() << ','
            << yaw.GetValue() << ',' << g.Left << ',' << g.Center << ',' << g.Right << ','
            << blobs.size() << ',' << cyan << ',' << filtered << ','
            << GetObjectiveFunction() << '\n';
    }
  }
};
REGISTER_LOOP_FUNCTIONS(ObservedMateCC, "observed_mate_cc");
