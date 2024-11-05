import asyncio
import json
from datetime import datetime
from typing import Dict, List

from kafka import KafkaConsumer, KafkaProducer
from pydantic import ValidationError

from app.core.config import settings
from app.models.schemas import KafkaMessage, VehicleData, PowerData, PlugStatus
from app.services.algorithm import AlgorithmService
from app.utils.logger import logger


class KafkaService:
    def __init__(self, algorithm_service: AlgorithmService):
        self.algorithm_service = algorithm_service
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3,
            retry_backoff_ms=1000
        )
        self.consumer = KafkaConsumer(
            *settings.KAFKA_TOPICS,
            bootstrap_servers=settings.KAFKA_SERVERS,
            group_id=settings.KAFKA_GROUP_ID,
            auto_offset_reset='latest',
            enable_auto_commit=False,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self._running = False

        async def _handle_message(self, message):
            """处理接收到的消息"""
            try:
                kafka_message = KafkaMessage(**message.value)

                if kafka_message.message_type == 1:
                    # 车型识别数据
                    vehicle_data = VehicleData(**kafka_message.data)
                    await self.algorithm_service.process_vehicle_data(vehicle_data)

                elif kafka_message.message_type == 2:
                    # 功率预测数据
                    power_data = PowerData(**kafka_message.data)
                    await self.algorithm_service.process_power_data(power_data)

                elif kafka_message.message_type == 3:
                    # 插拔枪状态
                    plug_status = PlugStatus(**kafka_message.data)
                    await self.algorithm_service.process_plug_status(plug_status)

                else:
                    logger.warning(f"未知的消息类型: {kafka_message.message_type}")

            except ValidationError as e:
                logger.error(f"消息格式验证失败: {str(e)}")
            except Exception as e:
                logger.error(f"消息处理失败: {str(e)}")

    async def start(self):
        """启动Kafka服务"""
        self._running = True
        await self.consume_messages()

    async def stop(self):
        """停止Kafka服务"""
        self._running = False
        self.producer.close()
        self.consumer.close()

    async def consume_messages(self):
        """消费Kafka消息"""
        try:
            while self._running:
                messages = self.consumer.poll(timeout_ms=1000)
                for topic_partition, records in messages.items():
                    for record in records:
                        await self._handle_message(record)
                        # 手动提交offset
                        self.consumer.commit()
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Kafka消息消费失败: {str(e)}")
            raise

    async def _handle_message(self, message):
        """处理接收到的消息"""
        try:
            data = message.value
            message_type = data.get('message_type')

            if message_type == 1:
                # 车型识别数据
                await self.algorithm_service.process_vehicle_data(data)
            elif message_type == 2:
                # 功率预测数据
                await self.algorithm_service.process_power_data(data)
            elif message_type == 3:
                # 插拔枪状态
                await self.algorithm_service.process_plug_status(data)
            else:
                logger.warning(f"未知的消息类型: {message_type}")

        except json.JSONDecodeError:
            logger.error("消息格式错误")
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}")

    async def publish_profile(self, profile: Dict):
        """发布充电配置信息"""
        try:
            topic = settings.KAFKA_TOPICS['POWER_ALLOCATION']
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'profile': profile,
                'version': '1.0'
            }
            future = self.producer.send(topic, message)
            await asyncio.wrap_future(future)
            logger.info(f"成功发布充电配置: {profile.get('charger_sn')}")
        except Exception as e:
            logger.error(f"发布充电配置失败: {str(e)}")
            raise

    async def publish_batch_profiles(self, profiles: List[Dict]):
        """批量发布充电配置信息"""
        try:
            for profile in profiles:
                await self.publish_profile(profile)
            logger.info(f"批量发布充电配置成功，数量: {len(profiles)}")
        except Exception as e:
            logger.error(f"批量发布充电配置失败: {str(e)}")
            raise
