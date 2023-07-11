
import torch
import torch.nn as nn

class UNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv2d = nn.Conv2d(1, 64, kernel_size=3, padding='same', padding_mode='zeros')
        self.conv2d_1 = nn.Conv2d(64, 64, kernel_size=3, padding='same')
        self.conv2d_2 = nn.Conv2d(64, 128, kernel_size=3, padding='same')
        self.conv2d_3 = nn.Conv2d(128, 128, kernel_size=3, padding='same')
        self.conv2d_4 = nn.Conv2d(128, 256, kernel_size=3, padding='same')
        self.conv2d_5 = nn.Conv2d(256, 256, kernel_size=3, padding='same')
        self.conv2d_6 = nn.Conv2d(256, 512, kernel_size=3, padding='same')
        self.conv2d_7 = nn.Conv2d(512, 512, kernel_size=3, padding='same')
        self.conv2d_8 = nn.Conv2d(512, 1024, kernel_size=3, padding='same')
        self.conv2d_9 = nn.Conv2d(1024, 1024, kernel_size=3, padding='same')
        self.conv2d_10 = nn.Conv2d(1024, 512, kernel_size=2, padding='same')
        self.conv2d_11 = nn.Conv2d(1024, 512, kernel_size=3, padding='same')
        self.conv2d_12 = nn.Conv2d(512, 512, kernel_size=3, padding='same')
        self.conv2d_13 = nn.Conv2d(512, 256, kernel_size=2, padding='same')
        self.conv2d_14 = nn.Conv2d(512, 256, kernel_size=3, padding='same')
        self.conv2d_15 = nn.Conv2d(256, 256, kernel_size=3, padding='same')
        self.conv2d_16 = nn.Conv2d(256, 128, kernel_size=2, padding='same')
        self.conv2d_17 = nn.Conv2d(256, 128, kernel_size=3, padding='same')
        self.conv2d_18 = nn.Conv2d(128, 128, kernel_size=3, padding='same')
        self.conv2d_19 = nn.Conv2d(128, 64, kernel_size=2, padding='same')
        self.conv2d_20 = nn.Conv2d(128, 64, kernel_size=3, padding='same')
        self.conv2d_21 = nn.Conv2d(64, 64, kernel_size=3, padding='same')
        self.conv2d_22 = nn.Conv2d(64, 2, kernel_size=3, padding='same')
        self.conv2d_23 = nn.Conv2d(2, 1, kernel_size=1, padding='same')

        # Other stuff
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool2d((2,2), stride=(2,2))
        self.dropout = nn.Dropout(0.5)
        self.upsample =  nn.Upsample(scale_factor=2, mode='nearest')
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs):
        """ Encoder """
        conv1 = self.conv2d(inputs)
        conv1 = self.relu(conv1)
        conv1 = self.conv2d_1(conv1)
        conv1 = self.relu(conv1)
        pool1 = self.maxpool(conv1)

        conv2 = self.conv2d_2(pool1)
        conv2 = self.relu(conv2)
        conv2 = self.conv2d_3(conv2)
        conv2= self.relu(conv2)
        pool2 = self.maxpool(conv2)

        conv3 = self.conv2d_4(pool2)
        conv3 = self.relu(conv3)
        conv3 = self.conv2d_5(conv3)
        conv3 = self.relu(conv3)
        pool3 = self.maxpool(conv3)

        conv4 = self.conv2d_6(pool3)
        conv4 = self.relu(conv4)
        conv4 = self.conv2d_7(conv4)
        conv4 = self.relu(conv4)
        drop4 = self.dropout(conv4)
        pool4 = self.maxpool(drop4)

        
        """ Bottleneck """
        conv5 = self.conv2d_8(pool4)
        conv5 = self.relu(conv5)
        conv5 = self.conv2d_9(conv5)
        conv5 = self.relu(conv5)
        drop5 = self.dropout(conv5)

        """ Decoder """
        up6 = self.upsample(drop5)
        up6 = self.conv2d_10(up6)
        up6 = self.relu(up6)
        merg6 = torch.cat((drop4,up6), dim=1)
        conv6 = self.conv2d_11(merg6)
        conv6 = self.relu(conv6)
        conv6 = self.conv2d_12(conv6)
        conv6 = self.relu(conv6)

        up7 = self.upsample(conv6)
        up7 = self.conv2d_13(up7)
        up7 = self.relu(up7)
        merg7 = torch.cat((conv3,up7), dim=1)
        conv7 = self.conv2d_14(merg7)
        conv7 = self.relu(conv7)
        conv7 = self.conv2d_15(conv7)
        conv7 = self.relu(conv7)

        up8 = self.upsample(conv7)
        up8 = self.conv2d_16(up8)
        up8 = self.relu(up8)
        merg8 = torch.cat((conv2,up8), dim=1)
        conv8 = self.conv2d_17(merg8)
        conv8 = self.relu(conv8)
        conv8 = self.conv2d_18(conv8)
        conv8 = self.relu(conv8)

        up9 = self.upsample(conv8)
        up9 = self.conv2d_19(up9)
        up9 = self.relu(up9)
        merg9 = torch.cat((conv1,up9), dim=1)
        conv9 = self.conv2d_20(merg9)
        conv9 = self.relu(conv9)
        conv9 = self.conv2d_21(conv9)
        conv9 = self.relu(conv9)

        """ Classifier """
        conv9 = self.conv2d_22(conv9)
        conv9 = self.relu(conv9)
        conv10 = self.conv2d_23(conv9)
        conv10 = self.sigmoid(conv10)
        
        
        return conv10

