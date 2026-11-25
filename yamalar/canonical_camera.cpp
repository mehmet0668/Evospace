#include <algorithm>
#include <cstdlib>
/**
 * @file <argos3/plugins/robots/e-puck/simulator/epuck_omnidirectional_camera_sensor.cpp>
 *
 * @author Gianpiero Francesca - <gianpiero.francesca@ulb.ac.be>
 * @author Lorenzo Garattoni - <lgaratto@ulb.ac.be>
 */
#include "epuck_omnidirectional_camera_sensor.h"
#include <argos3/core/simulator/simulator.h>
#include <argos3/core/simulator/space/positional_indices/positional_index.h>
#include <argos3/core/simulator/entity/composable_entity.h>
#include <argos3/core/simulator/entity/embodied_entity.h>
#include <argos3/plugins/simulator/entities/led_entity.h>
#include <argos3/plugins/simulator/entities/omnidirectional_camera_equipped_entity.h>
#include <argos3/plugins/simulator/media/led_medium.h>

namespace argos {

/****************************************/
/****************************************/

class CLEDCheckOperation : public CPositionalIndex<CLEDEntity>::COperation {

public:

    CLEDCheckOperation(CCI_EPuckOmnidirectionalCameraSensor::TBlobList& t_blobs,
                       COmnidirectionalCameraEquippedEntity& c_omnicam_entity,
                       CEmbodiedEntity& c_embodied_entity,
                       CControllableEntity& c_controllable_entity,
                       bool b_show_rays,Real f_distance_std_dev,CRandom::CRNG* pcRNG) :
        m_tBlobs(t_blobs),
        m_cOmnicamEntity(c_omnicam_entity),
        m_cEmbodiedEntity(c_embodied_entity),
        m_cControllableEntity(c_controllable_entity),
        m_bShowRays(b_show_rays),
        m_fDistanceNoiseStdDev(f_distance_std_dev),
        m_pcRNG(pcRNG){
        m_pcRootSensingEntity = &m_cEmbodiedEntity.GetParent();

    }
    virtual ~CLEDCheckOperation() {
        while(! m_tBlobs.empty()) {
            delete m_tBlobs.back();
            m_tBlobs.pop_back();
        }
    }

    virtual bool operator()(CLEDEntity& c_led) {
        /* Process this LED only if it's lit */
        if(c_led.GetColor() != CColor::BLACK) {
            if(c_led.HasParent()) {
                /* Filter out the LEDs belonging to the sensing entity by checking if they share the same parent entity */
                m_pcRootOfLEDEntity = &c_led.GetParent();
                while(m_pcRootOfLEDEntity->HasParent()) m_pcRootOfLEDEntity = &m_pcRootOfLEDEntity->GetParent();
                if(m_pcRootSensingEntity == m_pcRootOfLEDEntity) {
                    return true;
                }
            }
            /* If we are here, it's because the LED must be processed */
            m_cOcclusionCheckRay.SetEnd(c_led.GetPosition());
            m_cLEDRelativePos = c_led.GetPosition();
            m_cLEDRelativePos -= m_cCameraPos;
            m_cLEDRelativePosXY.Set(m_cLEDRelativePos.GetX(),
                                    m_cLEDRelativePos.GetY());
            if(Abs(m_cLEDRelativePos.GetX()) < m_fGroundHalfRange &&
                    Abs(m_cLEDRelativePos.GetY()) < m_fGroundHalfRange &&
                    m_cLEDRelativePos.GetZ() < m_cCameraPos.GetZ() &&
                    !GetClosestEmbodiedEntityIntersectedByRay(m_sIntersectionItem,
                                                              m_cOcclusionCheckRay,
                                                              m_cEmbodiedEntity)) {
                if(m_fDistanceNoiseStdDev > 0.0f) {
                    m_cLEDRelativePosXY += CVector2(
                                m_pcRNG->Gaussian(m_fDistanceNoiseStdDev),
                                m_pcRNG->Uniform(CRadians::UNSIGNED_RANGE));
                }
                Real fDistance=m_cLEDRelativePosXY.Length() * 100.0f;
                /*
                 * NOTE the area is calculated as 95.644*exp(-0.11f*fDistance). Such equation
                 * has been calculated from empirical data.
                   */
                m_tBlobs.push_back(new CCI_EPuckOmnidirectionalCameraSensor::SBlob(
                                       c_led.GetColor(),
                                       NormalizedDifference(m_cLEDRelativePosXY.Angle(), m_cCameraOrient),
                                       fDistance,95.644*exp(-0.11f*fDistance)));
                if(m_bShowRays) {
                    m_cControllableEntity.AddCheckedRay(false, CRay3(m_cCameraPos, c_led.GetPosition()));
                }
            }
        }
        return true;
    }

    void Setup(Real f_ground_half_range) {
        while(! m_tBlobs.empty()) {
            delete m_tBlobs.back();
            m_tBlobs.pop_back();
        }
        m_fGroundHalfRange = f_ground_half_range;
        m_cEmbodiedEntity.GetOriginAnchor().Orientation.ToEulerAngles(m_cCameraOrient, m_cTmp1, m_cTmp2);
        m_cCameraPos = m_cEmbodiedEntity.GetOriginAnchor().Position;
        m_cCameraPos += m_cOmnicamEntity.GetOffset();
        m_cOcclusionCheckRay.SetStart(m_cCameraPos);
    }

private:

    CCI_EPuckOmnidirectionalCameraSensor::TBlobList& m_tBlobs;
    COmnidirectionalCameraEquippedEntity& m_cOmnicamEntity;
    CEmbodiedEntity& m_cEmbodiedEntity;
    CControllableEntity& m_cControllableEntity;
    Real m_fGroundHalfRange;
    bool m_bShowRays;
    CEntity* m_pcRootSensingEntity;
    CEntity* m_pcRootOfLEDEntity;
    CVector3 m_cCameraPos;
    CRadians m_cCameraOrient;
    CRadians m_cTmp1, m_cTmp2;
    CVector3 m_cLEDRelativePos;
    CVector2 m_cLEDRelativePosXY;
    SEmbodiedEntityIntersectionItem m_sIntersectionItem;
    CRay3 m_cOcclusionCheckRay;
    Real              m_fDistanceNoiseStdDev;
    CRandom::CRNG*    m_pcRNG;

};

/****************************************/
/****************************************/


class StableLEDCollector : public CPositionalIndex<CLEDEntity>::COperation {
 public:
  CLEDEntity* items[1024]; unsigned count=0;
  bool operator()(CLEDEntity& led) override {
   if(count>=1024) std::abort();
   items[count++]=&led; return true;
  }
};
static bool StableLEDLess(CLEDEntity* a,CLEDEntity* b) {
 const std::string& ar=a->GetRootEntity().GetId();
 const std::string& br=b->GetRootEntity().GetId();
 if(ar!=br) {
  if(ar.compare(0,5,"epuck")==0 && br.compare(0,5,"epuck")==0)
   return std::atoi(ar.c_str()+5)<std::atoi(br.c_str()+5);
  return ar<br;
 }
 const std::string& ai=a->GetId(); const std::string& bi=b->GetId();
 if(ai.compare(0,4,"led_")==0 && bi.compare(0,4,"led_")==0)
  return std::atoi(ai.c_str()+4)<std::atoi(bi.c_str()+4);
 return ai<bi;
}
void CEPuckOmnidirectionalCameraSensor::Update() {
    if(m_bEnabled) {
        /* Increase data counter */
        ++m_sReadings.Counter;
        /* Calculate range on the ground */
        CVector3 cCameraPos = m_pcOmnicamEntity->GetOffset();
        cCameraPos += m_pcEmbodiedEntity->GetOriginAnchor().Position;
        Real fGroundHalfRange = cCameraPos.GetZ() * Tan(m_pcOmnicamEntity->GetAperture());
        /* Prepare the operation */
        m_pcOperation->Setup(fGroundHalfRange);
        /* Go through LED entities in box range */
        StableLEDCollector collector;
        m_pcLEDIndex->ForEntitiesInBoxRange(
                    CVector3(cCameraPos.GetX(),
                             cCameraPos.GetY(),
                             cCameraPos.GetZ() * 0.5f),
                    CVector3(fGroundHalfRange, fGroundHalfRange, cCameraPos.GetZ() * 0.5f),
                    collector);
        std::sort(collector.items,collector.items+collector.count,StableLEDLess);
        for(unsigned i=0;i<collector.count;++i) (*m_pcOperation)(*collector.items[i]);
    }
}

/****************************************/
/****************************************/


}
